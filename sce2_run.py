import os
import datetime
import argparse
from utils import *
from Scenario2.Agent import *
from Scenario2.Supervisor import *
from Scenario2.Prompt import *


def main(model_name):
    current_timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    savepath = f"Scenario2/log/{current_timestamp+'_'+model_name}"
    os.makedirs(savepath, exist_ok=True)

    iteration_count = 0

    A_vflag = True
    B_vflag = True
    A_policy = ""
    B_policy = ""
    A_plan = ""
    B_plan = ""
    pet_list = ["parrot", "cat", "lizard"]

    while iteration_count < 55:

        # round start and reset
        iteration_count += 1
        turn_count = 0
        round_savepath = f"{savepath}/{iteration_count}"
        os.makedirs(round_savepath, exist_ok=True)

        violation_log = load_violation_log(savepath, max_entries=20)
        violation_log_str = "".join(violation_log)

        pet = random.choice(pet_list)

        contextA, contextB, supervisor_context = create_prompts(
            pet, A_policy, B_policy, A_plan, B_plan, violation_log_str)

        supervisor = Supervisor(supervisor_context,
                                round_savepath,
                                model_name,
                                keyword_ban=True)
        agentA = Agent("A", contextA, round_savepath, model_name)
        agentB = Agent("B", contextB, round_savepath, model_name)

        if len(violation_log) >= 3:
            if A_vflag:
                agentA.summary_from_violation()
            if B_vflag:
                agentB.summary_from_violation()

        while turn_count < 4:
            write_log(f"===========Round {turn_count}===========",
                      round_savepath,
                      print_flag=True)
            turn_count += 1
            responseA = (agentA.reply(responseB, turn_count) if turn_count > 1
                         else agentA.start_conversation(turn_count))
            responseB = agentB.reply(responseA, turn_count)
            violation_text, A_vflag, B_vflag = supervisor.check_violation(
                responseA + "\n" + responseB + "\n")

            if violation_text != None:
                print(
                    "Dialogue interrupted by the supervisor, restarting the dialogue."
                )
                violation_log.append(violation_text)
                save_vlog(violation_log, savepath)
                policies = save_policy(agentA, agentB, dir=round_savepath)
                A_policy, B_policy = policies
                plans = save_advice(agentA, agentB, dir=round_savepath)
                A_plan, B_plan = plans

                print("=================End by Supervisor===================")
                print("=================End by Supervisor===================")
                print("=================End by Supervisor===================")
                new_round_savepath = f"{round_savepath}-{turn_count}"
                try_rename_dir(round_savepath, new_round_savepath)
                break

            #interview part
            if turn_count == 4:
                write_log("===========Interview===========", round_savepath)
                A_interview = agentA.interview_buyer()
                B_interview = agentB.interview_seller()

                write_log("===========Summary===========", round_savepath)
                buyer_flag = agentA.summary_from_result_buyer(B_interview)
                seller_flag = agentB.summary_from_result_seller(A_interview)
                result_flag = buyer_flag + seller_flag

                result_str = '-'.join(
                    ['1' if value else '0' for value in result_flag])

                print("Dialogue finished.")
                policies = save_policy(agentA, agentB, dir=round_savepath)
                A_policy, B_policy = policies
                plans = save_advice(agentA, agentB, dir=round_savepath)
                A_plan, B_plan = plans
                print("===================End by Agent=====================")
                print("===================End by Agent=====================")
                print("===================End by Agent=====================")
                new_round_savepath = f"{round_savepath}-{turn_count+1}--{result_str}"
                try_rename_dir(round_savepath, new_round_savepath)
                #input("Press Enter to continue...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the social media simulation scenario 2.')
    parser.add_argument('--model', type=str, choices=['gpt-3.5-turbo', 'gpt-4'], required=True,
                        help='The model to use: gpt-3.5-turbo or gpt-4.')
    args = parser.parse_args()

    main(args.model)
