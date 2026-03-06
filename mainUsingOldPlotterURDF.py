import os
import time
import pybullet as p
import pybullet_data


def link_index(body_id: int, link_name: str) -> int:
    """Returns the PyBullet link index (joint index whose child link has this name)."""
    for ji in range(p.getNumJoints(body_id)):
        if p.getJointInfo(body_id, ji)[12].decode("utf-8") == link_name:
            return ji
    raise ValueError(f"Link not found: {link_name}")


def main():
    p.connect(p.GUI)
    p.resetSimulation()
    p.setGravity(0, 0, -9.81)
    p.setTimeStep(1 / 240)

    # Closed loops need more solver effort
    p.setPhysicsEngineParameter(numSolverIterations=200)

    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.loadURDF("plane.urdf")

    here = os.path.dirname(os.path.abspath(__file__))
    p.setAdditionalSearchPath(here)

    urdf_path = os.path.join(here, "plotter.urdf")
    robotId = p.loadURDF(urdf_path, basePosition=[0, 0, 0], useFixedBase=True)

    p.resetDebugVisualizerCamera(
        cameraDistance=0.6,
        cameraYaw=45,
        cameraPitch=-30,
        cameraTargetPosition=[0, 0, 0],
    )

    # -------------------- CLOSED-LOOP: arm1_link <-> peg2_link (sticky) --------------------
    for _ in range(10):
        p.stepSimulation()

    arm1_idx = link_index(robotId, "arm1_link")
    peg2_idx = link_index(robotId, "peg2_link")

    # compute arm1-local pivot that matches peg2 origin now (no snapping)
    arm1_state = p.getLinkState(robotId, arm1_idx, computeForwardKinematics=True)
    peg2_state = p.getLinkState(robotId, peg2_idx, computeForwardKinematics=True)

    arm1_pos_w, arm1_orn_w = arm1_state[4], arm1_state[5]
    peg2_pos_w = peg2_state[4]

    inv_arm1_pos_w, inv_arm1_orn_w = p.invertTransform(arm1_pos_w, arm1_orn_w)
    peg2_in_arm1_pos, _ = p.multiplyTransforms(
        inv_arm1_pos_w, inv_arm1_orn_w,
        peg2_pos_w, [0, 0, 0, 1]
    )
    pivot_arm1 = list(peg2_in_arm1_pos)

    # two anchors to "stick" (approx weld but more stable than JOINT_FIXED)
    cid1 = p.createConstraint(
        robotId, arm1_idx,
        robotId, peg2_idx,
        p.JOINT_POINT2POINT,
        [0, 0, 0],
        pivot_arm1,
        [0, 0, 0]
    )

    offset = [0.0, 0.005, 0.0]  # 5mm separation to constrain orientation too
    cid2 = p.createConstraint(
        robotId, arm1_idx,
        robotId, peg2_idx,
        p.JOINT_POINT2POINT,
        [0, 0, 0],
        [pivot_arm1[0] + offset[0], pivot_arm1[1] + offset[1], pivot_arm1[2] + offset[2]],
        offset
    )

    for cid in (cid1, cid2):
        p.changeConstraint(cid, maxForce=300)  # try 300/800/1500
        p.changeConstraint(cid, erp=0.3)       # try 0.2–0.6

    # don't let their collisions fight the constraint
    p.setCollisionFilterPair(robotId, robotId, arm1_idx, peg2_idx, enableCollision=0)

    # small damping helps
    p.changeDynamics(robotId, arm1_idx, linearDamping=0.04, angularDamping=0.04)
    p.changeDynamics(robotId, peg2_idx, linearDamping=0.04, angularDamping=0.04)

    print("Loop constraints:", cid1, cid2)

    # -------------------- SLIDERS: ONLY DRIVE CAMS --------------------
    ACTUATED = {"cam_joint", "cam2_joint"}          # motors
    PASSIVE = {"peg1_joint", "peg2_joint", "peg3_joint"}  # bearings (free spin)

    sliders = {}
    motor_force_default = 3  # low force so it doesn't overpower the loop

    num = p.getNumJoints(robotId)
    print("Num joints:", num)

    for i in range(num):
        info = p.getJointInfo(robotId, i)
        jname = info[1].decode("utf-8")
        jtype = info[2]
        lower, upper = info[8], info[9]

        print(i, jname, "type:", jtype, "limits:", (lower, upper))

        if jtype == p.JOINT_FIXED:
            continue

        # Make bearing joints truly free-spinning
        if jname in PASSIVE:
            p.setJointMotorControl2(robotId, i, p.VELOCITY_CONTROL, force=0)
            continue

        # Only create sliders for actuated joints
        if jname not in ACTUATED:
            # also leave other joints passive unless you intentionally want to actuate them
            p.setJointMotorControl2(robotId, i, p.VELOCITY_CONTROL, force=0)
            continue

        start = 0.0 if (lower <= 0.0 <= upper) else (lower + upper) / 2
        sliders[i] = p.addUserDebugParameter(f"{jname} ({i})", lower, upper, start)

        # disable default motor so our control is clean
        p.setJointMotorControl2(robotId, i, p.VELOCITY_CONTROL, force=0)

    # -------------------- SIM LOOP --------------------
    try:
        while True:
            for joint_index, slider_id in sliders.items():
                target = p.readUserDebugParameter(slider_id)
                p.setJointMotorControl2(
                    robotId,
                    joint_index,
                    p.POSITION_CONTROL,
                    targetPosition=target,
                    force=motor_force_default
                )

            p.stepSimulation()
            time.sleep(1 / 240)

    except KeyboardInterrupt:
        pass
    finally:
        p.disconnect()


# if __name__ == "__main__":
#     main()