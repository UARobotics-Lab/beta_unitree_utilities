#include <array>
#include <chrono>
#include <iostream>
#include <thread>
#include <vector>
#include <string>

#include <unitree/idl/hg/LowCmd_.hpp>
#include <unitree/idl/hg/LowState_.hpp>
#include <unitree/robot/channel/channel_publisher.hpp>
#include <unitree/robot/channel/channel_subscriber.hpp>
#include <unitree/robot/g1/audio/g1_audio_client.hpp>

#define AUDIO_SUBSCRIBE_TOPIC "rt/audio_msg"
#define GROUP_IP "239.168.123.161"
#define PORT 5555

static const std::string kTopicArmSDK = "rt/arm_sdk";
static const std::string kTopicState = "rt/lowstate";
constexpr float kPi = 3.141592654;
constexpr float kPi_2 = 1.57079632;

enum JointIndex {
    // Left leg
    kLeftHipPitch,
    kLeftHipRoll,
    kLeftHipYaw,
    kLeftKnee,
    kLeftAnkle,
    kLeftAnkleRoll,

    // Right leg
    kRightHipPitch,
    kRightHipRoll,
    kRightHipYaw,
    kRightKnee,
    kRightAnkle,
    kRightAnkleRoll,

    kWaistYaw,
    kWaistRoll,
    kWaistPitch,

    // Left arm
    kLeftShoulderPitch,
    kLeftShoulderRoll,
    kLeftShoulderYaw,
    kLeftElbow,
    kLeftWristRoll,
    kLeftWristPitch,
    kLeftWristYaw,
    // Right arm
    kRightShoulderPitch,
    kRightShoulderRoll,
    kRightShoulderYaw,
    kRightElbow,
    kRightWristRoll,
    kRightWristPitch,
    kRightWristYaw,

    kNotUsedJoint,
    kNotUsedJoint1,
    kNotUsedJoint2,
    kNotUsedJoint3,
    kNotUsedJoint4,
    kNotUsedJoint5
};

int main(int argc, char const *argv[]) {
    if (argc < 2) {
        std::cout << "Usage: " << argv[0] << " networkInterface" << std::endl;
        exit(-1);
    }

    int32_t ret;
    //Inicializamos transmisión de canales
    unitree::robot::ChannelFactory::Instance()->Init(0, argv[1]);
    //Inicialización de arm_sdk
    unitree::robot::ChannelPublisherPtr<unitree_hg::msg::dds_::LowCmd_>
        arm_sdk_publisher;
    unitree_hg::msg::dds_::LowCmd_ msg;

    arm_sdk_publisher.reset(
        new unitree::robot::ChannelPublisher<unitree_hg::msg::dds_::LowCmd_>(
            kTopicArmSDK));
    arm_sdk_publisher->InitChannel();
    //Inicialización de API de audio y set de volúmen
    unitree::robot::g1::AudioClient client;
    client.Init();
    client.SetTimeout(10.0f);

    ret = client.SetVolume(100);
    std::cout << "SetVolume to 100% , API ret:" << ret << std::endl;

    unitree::robot::ChannelSubscriberPtr<unitree_hg::msg::dds_::LowState_>
        low_state_subscriber;

    // create subscriber
    unitree_hg::msg::dds_::LowState_ state_msg;
    low_state_subscriber.reset(
        new unitree::robot::ChannelSubscriber<unitree_hg::msg::dds_::LowState_>(
            kTopicState));
    low_state_subscriber->InitChannel([&](const void *msg) {
            auto s = ( const unitree_hg::msg::dds_::LowState_* )msg;
            memcpy( &state_msg, s, sizeof( unitree_hg::msg::dds_::LowState_ ) );
    }, 1);

    std::array<JointIndex, 17> arm_joints = {
        JointIndex::kLeftShoulderPitch,  JointIndex::kLeftShoulderRoll,
        JointIndex::kLeftShoulderYaw,    JointIndex::kLeftElbow,
        JointIndex::kLeftWristRoll,       JointIndex::kLeftWristPitch,
        JointIndex::kLeftWristYaw,
        JointIndex::kRightShoulderPitch, JointIndex::kRightShoulderRoll,
        JointIndex::kRightShoulderYaw,   JointIndex::kRightElbow,
        JointIndex::kRightWristRoll,      JointIndex::kRightWristPitch,
        JointIndex::kRightWristYaw,
        JointIndex::kWaistYaw,
        JointIndex::kWaistRoll,
        JointIndex::kWaistPitch};

    float weight = 0.f;
    float weight_rate = 0.2f;

    float kp = 60.f;
    float kd = 1.5f;
    float dq = 0.f;
    float tau_ff = 0.f;

    float control_dt = 0.02f;
    float max_joint_velocity = 0.5f;

    float delta_weight = weight_rate * control_dt;
    float max_joint_delta = max_joint_velocity * control_dt;
    auto sleep_time =
        std::chrono::milliseconds(static_cast<int>(control_dt / 0.001f));


    std::array<float, 17> init_pos{0, 0, 0, 0, 0, 0, 0,
                                    0, 0, 0, 0, 0, 0, 0,
                                    0, 0, 0};

    std::array<float, 17> target_pos = {0.f, kPi_2,  0.f, kPi_2, 0.f, 0.f, 0.f,
                                        0.f, -kPi_2, 0.f, kPi_2, 0.f, 0.f, 0.f, 
                                        0, 0, 0};

    // wait for init
    std::cout << "Press ENTER to init arms ...";
    std::cin.get();

    // get current joint position
    std::array<float, 17> current_jpos{};
    std::cout<<"Current joint position: ";
    for (int i = 0; i < arm_joints.size(); ++i) {
        current_jpos.at(i) = state_msg.motor_state().at(arm_joints.at(i)).q();
        std::cout << current_jpos.at(i) << " ";
    }
    std::cout << std::endl;

    

    // set init pos
    std::cout << "Initailizing arms ...";
    float init_time = 2.0f;
    int init_time_steps = static_cast<int>(init_time / control_dt);

    for (int i = 0; i < init_time_steps; ++i) {
        // increase weight
        weight = 1.0;
        msg.motor_cmd().at(JointIndex::kNotUsedJoint).q(weight);
        float phase = 1.0 * i / init_time_steps;
        std::cout << "Phase: " << phase << std::endl;

        // set control joints
        for (int j = 0; j < init_pos.size(); ++j) {
        msg.motor_cmd().at(arm_joints.at(j)).q(init_pos.at(j) * phase + current_jpos.at(j) * (1 - phase));
        msg.motor_cmd().at(arm_joints.at(j)).dq(dq);
        msg.motor_cmd().at(arm_joints.at(j)).kp(kp);
        msg.motor_cmd().at(arm_joints.at(j)).kd(kd);
        msg.motor_cmd().at(arm_joints.at(j)).tau(tau_ff);
        }

        // send dds msg
        arm_sdk_publisher->Write(msg);

        // sleep
        std::this_thread::sleep_for(sleep_time);
    }

    std::cout << "Done!" << std::endl;

    ret = client.TtsMaker(
      "Wellcome Hugo. Autogermana Innovation Manager. "
      "I'm G1. your smart robotic assistant. ",
      1);  // Engilsh TTS
    std::cout << "TtsMaker API ret:" << ret << std::endl;
    unitree::common::Sleep(3);

    // wait for control
    std::cout << "Press ENTER to start arm ctrl ..." << std::endl;
    std::cin.get();
    // start control
    std::cout << "Start arm ctrl!" << std::endl;
    float period = 5.f;
    int num_time_steps = static_cast<int>(period / control_dt);

    // Define tres posiciones objetivo
    std::array<float, 17> target_pos_1 = {
        0.f, kPi_2,  0.f, kPi_2, 0.f, 0.f, 0.f,
        0.f, -kPi_2, 0.f, kPi_2, 0.f, 0.f, 0.f,
        0, 0, 0
    };

    std::array<float, 17> target_pos_2 = {
        0.f, 0.f, 0.f, 0.f, 0.f, 0.f, 0.f,
        0.f, 0.f, 0.f, 0.f, 0.f, 0.f, 0.f,
        0.f, 0.f, 0.f
    };

    std::array<float, 17> target_pos_3 = {
        kPi_2, 0.f,  0.f, -kPi_2, 0.f, 0.f, 0.f,
        -kPi_2, 0.f, 0.f, -kPi_2, 0.f, 0.f, 0.f,
        0, 0, 0
    };

    // Lista de posiciones objetivo
    std::vector<std::array<float, 17>> targets = {target_pos_1, target_pos_2, target_pos_3};

    // Inicializar posición deseada
    std::array<float, 17> current_jpos_des{};

    // Función para mover hacia una posición objetivo
    auto move_to_target = [&](const std::array<float, 17>& target){
        for (int i = 0; i < num_time_steps; ++i) {
            // actualizar posición deseada
            for (int j = 0; j < init_pos.size(); ++j) {
                current_jpos_des.at(j) += std::clamp(
                    target.at(j) - current_jpos_des.at(j),
                    -max_joint_delta,
                    max_joint_delta
                );
            }

            // setear comando de motores
            for (int j = 0; j < init_pos.size(); ++j) {
                msg.motor_cmd().at(arm_joints.at(j)).q(current_jpos_des.at(j));
                msg.motor_cmd().at(arm_joints.at(j)).dq(dq);
                msg.motor_cmd().at(arm_joints.at(j)).kp(kp);
                msg.motor_cmd().at(arm_joints.at(j)).kd(kd);
                msg.motor_cmd().at(arm_joints.at(j)).tau(tau_ff);
            }

            // publicar
            arm_sdk_publisher->Write(msg);
            std::this_thread::sleep_for(sleep_time);
        }
    };

    std::cout << "Press ENTER to start 3-position arm ctrl ..." << std::endl;
    std::cin.get();

    ret = client.TtsMaker(
      "At Autogermana. passion and innovation move us. "
      "just like BMW  MINI and BMW Motorrad inspire the world.",
      1);  // Engilsh TTS
    std::cout << "TtsMaker API ret:" << ret << std::endl;
    unitree::common::Sleep(3);

    // Ejecutar movimientos
    for (const auto& target : targets) {
        std::cout << "Moving to next target position press ENTER..." << std::endl;
        std::cin.get();
        move_to_target(target);
        std::this_thread::sleep_for(std::chrono::seconds(2)); // espera entre posiciones
    }

    ret = client.TtsMaker(
      "I'm here to support our incredible staff. "
      "guiding visitors. assisting at events. and delivering information. ",
      1);  // Engilsh TTS
    std::cout << "TtsMaker API ret:" << ret << std::endl;
    unitree::common::Sleep(3);

    // Finalizar el control como antes
        // stop control
        std::cout << "Stoping arm ctrl ...";
        float stop_time = 2.0f;
        int stop_time_steps = static_cast<int>(stop_time / control_dt);

        for (int i = 0; i < stop_time_steps; ++i) {
        // increase weight
        weight -= delta_weight;
        weight = std::clamp(weight, 0.f, 1.f);

        // set weight
        msg.motor_cmd().at(JointIndex::kNotUsedJoint).q(weight);

        // send dds msg
        arm_sdk_publisher->Write(msg);

        // sleep
        std::this_thread::sleep_for(sleep_time);
        }
    ret = client.TtsMaker(
      "Together. we move emotions. and drive the future. ",
      1);  // Engilsh TTS
    std::cout << "TtsMaker API ret:" << ret << std::endl;
    unitree::common::Sleep(3);
    std::cout << "Done!" << std::endl;


    return 0;
}
