import os
import datetime
import argparse
from utils import *
from Scenario3.Agent import *
from Scenario3.Prompt import *
from Scenario3.Supervisor import *


def main(model_name):
    savepath = f"Scenario3/log/{current_timestamp+'_'+model_name}"
    current_timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    savepath = f"log/wastewater/{current_timestamp+'_'+model_name}"
    os.makedirs(savepath, exist_ok=True)

    iteration_count = 0
    violation_log = []
    contextA, contextB, contextC, contextD, supervisor_context = create_prompts(
    )

    supervisor = Supervisor(supervisor_context, savepath, 'gpt-3.5-turbo')
    agentA = Agent("Alice", contextA, savepath, model_name)
    agentB = Agent("Bob", contextB, savepath, model_name)
    agentC = Agent("Cindy", contextC, savepath, model_name)
    agentD = Agent("David", contextD, savepath, model_name)

    while True:
        # round start and reset
        iteration_count += 1
        round_savepath = f"{savepath}/{iteration_count}"
        os.makedirs(round_savepath, exist_ok=True)

        supervisor.savepath = round_savepath
        agentA.savepath = round_savepath
        agentB.savepath = round_savepath
        agentC.savepath = round_savepath
        agentD.savepath = round_savepath

        forum = Forum([agentA, agentB, agentC, agentD], supervisor,
                      round_savepath, violation_log)

        forum.conduct_forum()
        violation_log = forum.violation_log
        savelog(violation_log, round_savepath + "./violation_log.txt")
        savelog(forum.dialogue_history, round_savepath + "./dialogue.txt")
        try_count = forum.try_count
        summary_count = forum.summary_count
        new_round_savepath = f"{round_savepath}-{try_count}-{summary_count}"
        try_rename_dir(round_savepath, new_round_savepath)


class Forum:

    def __init__(self, agents, supervisor, savepath, violation_log=[]):
        self.agents = agents
        self.request_list = [True for agent in agents]
        self.supervisor = supervisor
        self.dialogue_history = []
        self.savepath = savepath
        self.violation_log = violation_log
        self.round_count = 0
        self.current_turn = 0
        self.try_count = 0
        self.summary_count = 0

    def conduct_forum(self):
        last_agent = None
        while not self.is_forum_over():
            current_agent = self.select_next_agent(last_agent)
            if self.dialogue_history == []:
                response = current_agent.start_conversation()
                self.try_count += 1
            else:
                response = current_agent.reply(self.dialogue_history)
                self.try_count += 1
            if response == None:
                continue

            print(current_agent.name + " said: " + response)
            if self.handle_response(response, current_agent):
                print(
                    f"==================Turn {self.current_turn}=================="
                )
                self.dialogue_history.append(current_agent.name + " said: " +
                                             response + "\n")
                self.current_turn += 1
                last_agent = current_agent
            #else:
            #    red_print(current_agent.name + " violated the rules.")

        self.summary_part()

    def select_next_agent(self, last_agent):
        if not any(self.request_list):
            self.request_list = [True for agent in self.agents]
            self.round_count += 1

        for index, agent in enumerate(self.agents):
            if self.request_list[index]:
                self.request_list[index] = False
                if agent == last_agent:
                    return self.select_next_agent(last_agent)
                else:
                    return agent

        raise Exception("No agent is available")

    def handle_response(self, response, current_agent):
        violation_text = self.supervisor.check_violation(response)
        if violation_text != None:
            self.violation_log.append(violation_text)
            current_agent.summary_from_violation(self.violation_log[-20:])
            return False
        else:
            return True

    def summary_part(self):
        for agent in self.agents:
            is_pass = agent.summary_from_dialogue(self.dialogue_history)
            if is_pass:
                self.summary_count += 1
        return

    def is_forum_over(self):
        if self.current_turn >= 10:
            return True
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the social media simulation scenario 3.')
    parser.add_argument('--model', type=str, choices=['gpt-3.5-turbo', 'gpt-4'], required=True,
                        help='The model to use: gpt-3.5-turbo or gpt-4.')
    args = parser.parse_args()

    main(args.model)
