import pybullet as p
import pybullet_data
import time
import os

# Joint / Link indices
# Joint 0: world_to_base   type=4 (FIXED)
# Joint 1: Revolute 9      type=0  <- cam2   (stepper 1)   child = cam2_1
# Joint 2: Rigid 20        type=4 (FIXED)   <- link3 fixed to cam2  child = link3_1
# Joint 3: Revolute 10     type=0  <- cam    (stepper 2)   child = cam_1
# Joint 4: Revolute 15     type=0  <- link1  (free bearing) child = link1_1
# Joint 5: Revolute 18     type=0  <- link2  (free bearing) child = link2_1

JOINT_CAM2  = 1
JOINT_CAM   = 3
JOINT_LINK1 = 4
JOINT_LINK2 = 5

LINK_LINK3  = 2   # child of Rigid 20
LINK_LINK2  = 5   # child of Revolute 18

# Loop closure pivots in LOCAL frames, derived from URDF:
#
# link3 (Rigid 20, no rotation from cam2):
#   local axes match base_link. link3 CoM at local z=-0.1167 so extends in -Z.
#   Peg is 175mm from link3 origin -> pivot at local z = -0.175
#
# link2 (Revolute 18 child):
#   link2 CoM at local x=-0.143 -> extends in -X.
#   Revolute 18 is at the link1-end hole (link2 origin).
#   The link3-end hole (loop closure) is 50mm away -> local x = -0.05

PIVOT_ON_LINK3 = [ 0.0,   0.0, -0.175]
PIVOT_ON_LINK2 = [-0.05,  0.0,  0.0  ]


def main():
    URDF_PATH = os.path.join(
        os.path.dirname(__file__),
        "penplotter_description", "urdf", "penplotter.xacro"
    )

    p.connect(p.GUI)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)
    p.setPhysicsEngineParameter(
        numSolverIterations=200,
        numSubSteps=4,
    )
    p.resetDebugVisualizerCamera(
        cameraDistance=0.6,
        cameraYaw=45,
        cameraPitch=-30,
        cameraTargetPosition=[0, 0, 0.1],
    )

    p.loadURDF("plane.urdf")

    robot_id = p.loadURDF(
        URDF_PATH,
        basePosition=[0, 0, 0],
        useFixedBase=True,
        flags=p.URDF_USE_INERTIA_FROM_FILE,
    )

    print(f"\nLoaded robot_id = {robot_id}")
    print(f"Number of joints: {p.getNumJoints(robot_id)}\n")
    for i in range(p.getNumJoints(robot_id)):
        info = p.getJointInfo(robot_id, i)
        print(f"  Joint {info[0]:>2}: {info[1].decode():<30}  type={info[2]}")

    # Disable default motor damping on free-bearing joints
    for joint in [JOINT_LINK1, JOINT_LINK2]:
        p.setJointMotorControl2(
            robot_id, joint,
            controlMode=p.VELOCITY_CONTROL,
            targetVelocity=0,
            force=0,
        )

    # Loop closure constraint: link3 peg <-> link2 second hole
    p.stepSimulation()  # initialise link states first

    loop_constraint = p.createConstraint(
        robot_id,             # parentBodyUniqueId
        LINK_LINK3,           # parentLinkIndex  (link3_1)
        robot_id,             # childBodyUniqueId
        LINK_LINK2,           # childLinkIndex   (link2_1)
        p.JOINT_POINT2POINT,  # jointType
        [0, 0, 1],            # jointAxis (unused for point2point)
        PIVOT_ON_LINK3,       # parentFramePosition in link3 local frame
        PIVOT_ON_LINK2,       # childFramePosition  in link2 local frame
    )

    p.changeConstraint(loop_constraint, maxForce=500, erp=0.8)

    print(f"\nLoop closure constraint created (id={loop_constraint})")
    print(f"  pivot_on_link3 : {PIVOT_ON_LINK3}  (175mm along link3 local -Z)")
    print(f"  pivot_on_link2 : {PIVOT_ON_LINK2}  (50mm along link2 local -X)")
    print("\nSimulation running - close PyBullet window or Ctrl-C to quit\n")

    cam2_slider = p.addUserDebugParameter("cam2 angle", -3.14159, 3.14159, 0)
    cam_slider  = p.addUserDebugParameter("cam angle",  -3.14159, 3.14159, 0)

    try:
        while True:
            cam2_pos = p.readUserDebugParameter(cam2_slider)
            cam_pos  = p.readUserDebugParameter(cam_slider)

            p.setJointMotorControl2(
                robot_id, JOINT_CAM2,
                p.POSITION_CONTROL,
                targetPosition=cam2_pos,
                force=50,
                maxVelocity=2.0,
            )
            p.setJointMotorControl2(
                robot_id, JOINT_CAM,
                p.POSITION_CONTROL,
                targetPosition=cam_pos,
                force=50,
                maxVelocity=2.0,
            )

            p.stepSimulation()
            time.sleep(1.0 / 240.0)

    except KeyboardInterrupt:
        pass
    finally:
        p.disconnect()


if __name__ == "__main__":
    main()
