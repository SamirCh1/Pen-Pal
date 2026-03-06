import pybullet as p
import pybullet_data
import time
import os

def main():
    URDF_PATH = os.path.join(
        os.path.dirname(__file__),
        "penplotter_description", "urdf", "penplotter.xacro"
    )

    p.connect(p.GUI)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)

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

    # Loop closure constraint: link3 (2) <-> link2 (5)
    # constraint_id = p.createConstraint(
    #     parentBodyUniqueId=robot_id,
    #     parentLinkIndex=2,        # link3
    #     childBodyUniqueId=robot_id,
    #     childLinkIndex=5,         # link2
    #     jointType=p.JOINT_POINT2POINT,
    #     jointAxis=[0, 0, 0],
    #     parentFramePosition=[0, 0, 0.175],
    #     childFramePosition=[-0.05, 0, 0],
    # )
    # p.changeConstraint(constraint_id, maxForce=500)

    print("\nSimulation running – close the PyBullet window or Ctrl-C to quit\n")

    # Add sliders for the two stepper motors
    cam2_slider = p.addUserDebugParameter("cam2 angle", -3.14, 3.14, 0)
    cam_slider  = p.addUserDebugParameter("cam angle",  -3.14, 3.14, 0)

    try:
        while True:
            cam2_pos = p.readUserDebugParameter(cam2_slider)
            cam_pos  = p.readUserDebugParameter(cam_slider)

            p.setJointMotorControl2(robot_id, 1, p.POSITION_CONTROL, targetPosition=cam2_pos, force=10)
            p.setJointMotorControl2(robot_id, 3, p.POSITION_CONTROL, targetPosition=cam_pos,  force=10)

            p.stepSimulation()
            time.sleep(1.0 / 240.0)
    except KeyboardInterrupt:
        pass

# if __name__ == "__main__":
#     main()