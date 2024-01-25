import os
import datetime
import argparse
from Scenario1.Agent import *
from Scenario1.Prompt import *
from Scenario1.Supervisor import *
from utils import *

def main(model_name):
    current_timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    savepath = f"Scenario1/log/{current_timestamp+'_'+model_name}"
    os.makedirs(savepath, exist_ok=True)

    A_number = 58
    B_number = 32
    iteration_count = 0

    A_vflag = True
    B_vflag = True
    A_policy = ""
    B_policy = ""
    A_advice = ""
    B_advice = ""

    while True:

        # round start and reset
        iteration_count += 1
        round_count = 0
        round_file_path = f"{savepath}/{iteration_count}"
        os.makedirs(round_file_path, exist_ok=True)

        #A_number = random.randint(1, 100)
        #B_number = random.randint(1, 100)

        violation_log = load_violation_log(savepath, max_entries=20)
        violation_log_str = "".join(violation_log)

        contextA, contextB, supervisor_context = create_prompts(
            A_number, B_number, A_policy, B_policy, A_advice, B_advice,
            violation_log_str)

        supervisor = Supervisor(supervisor_context, round_file_path,
                                "gpt-3.5-turbo")
        agentA = Agent("A", contextA, round_file_path, model_name, A_number)
        agentB = Agent("B", contextB, round_file_path, model_name, B_number)

        if len(violation_log) >= 3:
            if A_vflag:
                agentA.summary_from_violation()
            if B_vflag:
                agentB.summary_from_violation()

        while round_count < 5:
            print(f"==================Round {round_count}==================")
            round_count += 1
            responseA = (agentA.reply(responseB, round_count) if round_count
                         > 1 else agentA.start_conversation(round_count))
            responseB = agentB.reply(responseA, round_count)
            violation_text, A_vflag, B_vflag = supervisor.check_violation(
                responseA + "\n" + responseB + "\n")

            if violation_text != None:
                print(
                    "Dialogue interrupted by the supervisor, restarting the dialogue."
                )
                violation_log.append(violation_text)
                save_vlog(violation_log, savepath)
                policies = save_policy(agentA, agentB, dir=round_file_path)
                A_policy, B_policy = policies
                advices = save_advice(agentA, agentB, dir=round_file_path)
                A_advice, B_advice = advices

                print("=================End by Supervisor===================")
                print("=================End by Supervisor===================")
                print("=================End by Supervisor===================")
                new_round_file_path = f"{round_file_path}-{round_count}"
                os.rename(round_file_path, new_round_file_path)
                break

            #interview part
            if round_count == 5:
                A_interview, gussed_b_number = agentA.interview_num()
                B_interview, gussed_a_number = agentB.interview_num()

                A_acc = calculate_accuracy(gussed_b_number, B_number)
                B_acc = calculate_accuracy(gussed_a_number, A_number)

                agentA.summary_from_result_number(B_interview)
                agentB.summary_from_result_number(A_interview)
                print("Dialogue finished.")
                policies = save_policy(agentA, agentB, dir=round_file_path)
                A_policy, B_policy = policies
                advices = save_advice(agentA, agentB, dir=round_file_path)
                A_advice, B_advice = advices
                print("===================End by Agent=====================")
                print("===================End by Agent=====================")
                print("===================End by Agent=====================")
                new_round_file_path = f"{round_file_path}-{round_count+1}--{gussed_a_number}-{gussed_b_number}"
                rename_dir(round_file_path, new_round_file_path)
                #input("Press Enter to continue...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the social media simulation scenario 1.')
    parser.add_argument('--model', type=str, choices=['gpt-3.5-turbo', 'gpt-4'], required=True,
                        help='The model to use: gpt-3.5-turbo or gpt-4.')
    args = parser.parse_args()

    main(args.model)