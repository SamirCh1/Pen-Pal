use std::{collections::HashMap, sync::{atomic::{AtomicU64, Ordering}, Arc}};
use axum::{
    extract::{ws::{Message, WebSocket, WebSocketUpgrade}, State},
    http::{HeaderMap, StatusCode},
    response::IntoResponse,
    routing::{any, get, post},
    Router,
};
use futures_util::{sink::SinkExt, stream::{StreamExt}};
use serde::{Deserialize, Serialize};
use tokio::sync::mpsc::{self, UnboundedReceiver};
use tokio::sync::RwLock;
use base64::{engine::general_purpose::URL_SAFE, Engine};

#[derive(Deserialize)]
#[serde(tag = "type", rename_all = "SCREAMING_SNAKE_CASE")]
enum ClientMessage {
    Submit {
        session_id: u64,
        svg: String
    }
}

#[derive(Serialize, Clone)]
#[serde(tag = "type", rename_all = "SCREAMING_SNAKE_CASE")]
enum ServerMessage {
    StartSession {
        session_id: u64
    },
    Turn {
        session_id: u64
    },
    Draw {
        session_id: u64,
        svg: String
    },
    Error
}

#[derive(Clone)]
enum ConnectedDeviceState {
    Idle,
    InSession
}

#[derive(Clone)]
struct ConnectedDevice {
    account_id: u64,
    tx_chan: mpsc::UnboundedSender<ServerMessage>,
    state: ConnectedDeviceState,
    session_id: Option<u64>
}

#[derive(Clone)]
enum SessionState {
    Pending,
    Active,
    Ended
}

#[derive(Clone)]
struct Session {
    id: u64,
    device_a: u64,
    device_b: u64,
    state: SessionState,
    turn_device: u64
}

#[derive(Clone)]
struct AppState {
    // Maps device_id to ConnectedDevice struct
    device_conns: Arc<RwLock<HashMap<u64, ConnectedDevice>>>,
    sessions: Arc<RwLock<HashMap<u64, Session>>>,
    next_sid: Arc<AtomicU64>
}

fn authenticate_device(device_token: &[u8]) -> Option<(u64, u64)> {
    // TODO: do actual lookup, probably in a DB
    if device_token[0] == 0 {
        Some((1, 1))
    } else if device_token[0] == 1 {
        Some((2, 2))
    } else {
        None
    }
}

async fn ws_upgrade_handler(ws: WebSocketUpgrade, State(state): State<AppState>, headers: HeaderMap) -> impl IntoResponse {
    let Some(auth_header) = headers.get("Authorization") else {
        return (StatusCode::BAD_REQUEST, "Missing authorization").into_response();
    };

    let Ok(token) = auth_header.to_str() else {
        return (StatusCode::UNAUTHORIZED, "Invalid Token").into_response();
    };
    
    let Ok(token_decoded) = URL_SAFE.decode(token) else {
        return (StatusCode::BAD_REQUEST, "Invalid Token").into_response();
    };

    let Some((device_id, account_id)) = authenticate_device(&token_decoded[..]) else {
        return (StatusCode::UNAUTHORIZED, "Unauthorized").into_response();
    };

    let mut conns = state.device_conns.write().await;

    if conns.contains_key(&device_id) {
        // already connected, reject connection
        return (StatusCode::CONFLICT, "Already connected on another websocket").into_response();
    };

    let (tx, rx) = mpsc::unbounded_channel::<ServerMessage>();
    conns.insert(device_id, ConnectedDevice {
        account_id: account_id,
        tx_chan: tx,
        state: ConnectedDeviceState::Idle,
        session_id: None
    });

    // We have to drop the lock explicitly to prevent it from being borrowed
    // so we can move it into the closure
    drop(conns);

    ws.on_upgrade(move |socket| handle_ws(socket, state, rx, device_id))
}

fn get_other(device: u64, device_a: u64, device_b: u64) -> u64 {
    if device == device_a {
        device_b
    } else {
        device_a
    }
}

async fn handle_client_message(msg: &ClientMessage, device_id: u64, app_state: &AppState) {
    match msg {
        ClientMessage::Submit { session_id, svg } => {
            // Lookup session_id
            let conns = app_state.device_conns.read().await;
            let dev = conns.get(&device_id).unwrap();

            let sid = match dev.session_id {
                Some(s) => s,
                None => return // error here
            };

            if sid != *session_id {
                return; // another error here
            }

            let mut sessions = app_state.sessions.write().await;
            let session = sessions.get_mut(&sid).unwrap();

            let other_device = get_other(device_id, session.device_a, session.device_b);
            session.turn_device = other_device;

            drop(conns);

            send_to_device(app_state, other_device, ServerMessage::Draw { session_id: sid, svg: svg.clone() }).await;
            send_to_device(app_state, other_device, ServerMessage::Turn { session_id: sid }).await;
        }
    }
}

async fn handle_ws(socket: WebSocket, app_state: AppState, mut rx_chan: UnboundedReceiver<ServerMessage>, device_id: u64) {
    let (mut sender, mut receiver) = socket.split();

    tokio::spawn(async move {
        while let Some(msg) = rx_chan.recv().await {
            let json = serde_json::to_string(&msg).unwrap();
            if sender.send(json.into()).await.is_err() {
                break;
            }
        }
    });

    while let Ok(msg) = receiver.next().await.unwrap() {
        match msg {
            Message::Text(text) => {
                let parsed = match serde_json::from_str::<ClientMessage>(&text) {
                    Ok(p) => p,
                    Err(_) => {
                        // TODO: handle invalid message
                        continue;
                    }
                };
                handle_client_message(&parsed, device_id, &app_state).await;
            },

            Message::Close(_) => break,

            // TODO: handle invalid messages (Binary)
            _ => {}
        }
    }
    
    let mut conns = app_state.device_conns.write().await;
    conns.remove(&device_id);
}

async fn send_to_device(state: &AppState, device_id: u64, msg: ServerMessage) {
    let conns = state.device_conns.read().await;

    let Some(dev) = conns.get(&device_id) else {
        return;
    };

    dev.tx_chan.send(msg).unwrap();
}

async fn try_start_session(state: &AppState, session_id: u64) {
    let mut sessions = state.sessions.write().await;
    let mut conns = state.device_conns.write().await;

    let Some(session) = sessions.get_mut(&session_id) else {
        return;
    };

    let a_online = conns.contains_key(&session.device_a);
    let b_online = conns.contains_key(&session.device_b);

    if !a_online || !b_online {
        return;
    }

    conns.get_mut(&session.device_a).unwrap().session_id = Some(session_id);
    conns.get_mut(&session.device_b).unwrap().session_id = Some(session_id);

    session.state = SessionState::Active;

    // dodgy but works for now
    drop(conns);

    let start = ServerMessage::StartSession { session_id: session_id };
    send_to_device(state, session.device_a, start.clone()).await;
    send_to_device(state, session.device_b, start).await;
    
    send_to_device(state, session.turn_device, ServerMessage::Turn { session_id: session_id }).await;
}

async fn start_session_handler(State(state): State<AppState>) -> impl IntoResponse {
    // Pretend that we have looked up two users and got their device ids,
    // and also assume these devices are online
    let device_a = 1;
    let device_b = 2;
    let sid = state.next_sid.fetch_add(1, Ordering::Relaxed);

    {
        let mut sessions = state.sessions.write().await;
        sessions.insert(sid, Session {
            id: sid,
            device_a: device_a,
            device_b: device_b,
            state: SessionState::Pending,
            turn_device: device_a
        });
    }

    try_start_session(&state, sid).await;

    (StatusCode::OK, "ok")
}

#[tokio::main]
async fn main() {
    let state = AppState {
        device_conns: Arc::new(RwLock::new(HashMap::new())),
        sessions: Arc::new(RwLock::new(HashMap::new())),
        next_sid: Arc::new(AtomicU64::new(1))
    };

    let app = Router::new()
        .route("/ws", any(ws_upgrade_handler))
        .route("/dummy_start", post(start_session_handler)) // dummy route, fix later
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await.unwrap();
    axum::serve(listener, app).await.unwrap();
}


