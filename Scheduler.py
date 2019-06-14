'''
Fantasy Football Scheduler
Author: Ben Parisi

The impetus behind the creation of this program was the desire for a custom scheduler that could be used
to construct random schedules between a certain (even) number of teams in a fantasy football league.
Thus, in its current form, the program expects as input a number of weeks (however long your fantasy
football regular season may be), followed by a list of space-separated team names or some other identifier.

The program then constructs a schedule in which each team plays every other team at least once (provided
there are enough total weeks to allow that) before a repeat match is played between any two teams.

If there are weeks remaining to schedule after that, the process is repeated, so each team would have to
play every other team twice before any team plays an opponent for a third time, etc.

As it is, the program could be used for any similar scheduling scenario outside of fantasy football,
namely any similar round-robin style tournament. Just replace 'week' with 'round'.

With a little adaptation, the core algorithm (90% of which is contained in the runScheduler() function,
with assists from the testMatch() and setIsUnique() functions) could be used for a variety of other
scheduling purposes, or more broadly might find use in any task that must generate unique pairs or
permutations from within a set.

As an additional note, if you enter N 'teams' to be scheduled over N-1 'weeks', the result is essentially
an NxN grid in which every row and every column of the grid contains exactly one instance of each team.
There are easier ways to construct such a grid, since this program must also abide by the stipulation
that, for instance, if index 1 in row A is 'C', then index 1 of row C must be 'A' (if A is playing C
that week, then C must play A and no one else). Still, the functionality is there.

The core algorithm works roughly as follows:

First of all, each team maintains a set that keeps track of which other teams it has already played.
With that in mind:
1) A new week is started.
2) A random team is selected from all teams that have not yet been scheduled this week.
3) The chosen team's potential matches are identified based its already_played_set in comparison to
    the remaining unscheduled teams. (unscheduled_set - already_played_set)
    
4) The list of potential matches is then iterated through, and in order to remain on the list, a
    potential match being removed from the list of unscheduled teams must NOT result in any of the
    remaining unscheduled teams having no valid matches left. This is determined to be true if
    the would-be set of unscheduled teams forms a subset of any unscheduled team's already_played_set,
    with that team included. So if the remaining unscheduled teams would be {A, B, C, D}, and team
    A's already_played_set includes {B, C, D}, then the potential match is invalid.
    It might be expressed in psuedo-code as (unscheduled_teams <= already_played_set.union({self}))
    
5) The list of potential matches is further refined, but this time matches that do not meet the
    requirements are not eliminated, but only listed as not preferred. The requirement here is
    that once each team in a potential match adds the other team to its already_played_set, all
    already_played_sets between all teams that have already been scheduled this week are unique.
    If any two already_played_sets are the same, the match is not preferred, but we may still be
    forced to use it if all potential matches turn out to be not preferred.
    This step cuts down on situations such as:
    A - {C, D, E}
    B - {D, E, C}
    C - {A, F, B}
    D - {B, A, F}
    E - {F, B, A}
    F - {E, C, D}
    In this situation, team A must next choose either B or F to play, but no matter which one is chosen,
    the other will have no valid matches left to choose from, thus ensuring a failure and a restart.
    Preferring unique sets means that once A had chosen E for its third matchup, team B prefers not
    to choose team C, and instead would choose team F, preserving unique sets and, at least for now,
    the possibility of successful completion. More info on the possibility of failure is below.
    
6) If possible, a preferred match is chosen and recorded, or else a non-preferred match is chosen.
    Each team officially adds the other to its schedule and already_played_set, and are removed from
    unscheduled_teams and added to scheduled_teams if they have not been already.
7) Repeat steps 2-6 until all teams are matched for the week.
8) Repeat steps 1-7 until all weeks have been scheduled.



ON THE POSSIBILITY OF FAILURE
I undertook this project as a personal endeavor to challenge myself and did not do any research into
existing scheduling algorithms. For all I know, there exists another algorithm which serves the same
purpose and never fails. However, I came up with a process that seemed logical to me, and attempted
to execute it. Once I started down the rabbit hole of examining situations in which the algorithm runs
itself into a corner and there is no unscheduled team which would not be a repeat matchup, it became
apparent that without going to the lengths of formal proof, there were probably more ways to end up
at such a dead end than I could hope to account for.

Step 5 above touches on one such way, but since it looks only one step ahead, it cannot prevent all
occurences of that pattern. It seemed to me that without an overly complicated system which looked
very far ahead without actually committing to anything, the possibility of failure remained. Rather
than scrap the algorithm and attempt to come up with an entirely different approach, I decided I
might as well just loop the algorithm to reset and try again when it gets stuck, since the failure
rate was seemingly low enough that an excessive amount of reset-looping would not occur.

To aid in examining the failure rate, I have included a debug mode in the program. By entering
'debug' the first time you are prompted for a number of weeks, the program will switch to debug
mode and rather than spit out the schedule when it is done, it will ask for a number of trials,
and then run until that many trials have successfully produced schedules of the desired length.
The program will then report on the number of resets that were necessary before each successful
attempt, showing stats such as the max number of resets, the average number of resets, etc.

Determined through the use of this debug mode, it seems to me that step 5 in the algorithm above
reduces the average number of resets needed by about 0.5.
'''


import random
from statistics import mean
from math import ceil

#global vars used for debug mode
retries_needed = 0
data = []

class Team:
    '''The main class defining a member of the schedule'''
    def __init__(self, owner):            
        self.name = owner
        self.schedule = []
        self.already_played_set = set()
    def printSchedule(self):
        print(self.name, "{", end=' ')
        for i in range(len(self.schedule)):
            print(self.schedule[i], ',', end=' ')
        print("}")

class WeeklySchedule:
    '''A class which keeps track of matchups week-by-week rather than team-by-team'''
    def __init__(self):
        self.schedule = []
        self.next_index = 0
    def printSchedule(self):
        for i in range(len(self.schedule)):
            print(f"Week {i+1}\n-------------")
            print(self.schedule[i], "\n")
        
def testMatch(match, unscheduled_teams):
    '''Tests if removing 'match' from 'unscheduled_teams' would result in the
    remaining unscheduled_teams forming a subset of any other unscheduled_team's
    already_played_set (with themselves added to that set)'''
                
    test_set = set(unscheduled_teams)
    test_set.remove(match) #now the set of all other unscheduled teams
    for team in test_set:
        #construct set for comparison
        set1 = team.already_played_set | set([team])
        if (test_set <= set1):
            return False
    #if the loop completes without returning...
    return True

def setIsUnique(a_set, teams):
    '''Returns true if no equivalent sets to 'a_set' are found in any team'''
    for team in teams:
        if team.already_played_set == set(a_set):
            return False
    #if the loop completes without returning...
    return True
    

def setMatchForTeam(team1, team2):
    '''A convenience function for once a match has been determined'''
    team1.schedule.append(team2.name)
    team2.schedule.append(team1.name)
    team1.already_played_set.add(team2)
    team2.already_played_set.add(team1)


def getTeamByName(name, allTeams):
    '''Convenient utility function, currently unused'''
    return [a for a in allTeams if a.name == name].pop()

def printAllSets(allTeams):
    '''Convenient utility function, made for debugging, currently unused'''
    for team in allTeams:
        print(f"{team.name}:", {a.name for a in team.already_played_set})

def validatePosIntInput(val):
    '''A function that validates input as a positive integer'''
    requires_reentry = True

    while (requires_reentry):
        try:
            val = int(val)
            while val < 1:
                print("The number must be greater than 0, or there is no point.")
                val = input("Re-enter number --> ").strip()
                val = int(val)
            requires_reentry = False
        except ValueError:
            print("Please enter a valid number greater than 0.")
            val = input("Re-enter number --> ").strip()

    return val


#MAIN FUNCTIONS

def metaWrapper():
    '''Wrapped around the whole program for running debug mode multiple times'''
    retVal = preMain()
    while retVal: retVal = preMain()
    temp = input("Press any key to end")
    print("\nGoodbye.")

def preMain():
    '''This function handles initial input and sets up the variables needed by the Scheduler'''
    global retries_needed
    global data
    data = []

    #WEEKS / DEBUG MODE
    print("\nWelcome to the Fantasy Football Scheduler!")
    weeks = input("How many weeks should be scheduled? --> ").strip()
    debug_mode = True if weeks == "debug" else False

    if (debug_mode):
        print("[DEBUG MODE ACTIVATED]")
        weeks = input("How many weeks should be scheduled? --> ").strip()
    
    weeks = validatePosIntInput(weeks)

    #TEAM NAMES
    print("Enter names of teams, space-separated.")
    names = input("--> ").strip().split()

    while (len(names) % 2 != 0 or len(names) == 0):
        print("There must be a positive even number of teams! Please re-enter names.")
        names = input("--> ").strip().split()


    #PROGRAM EXECUTION
    if (debug_mode):
        trials = input("[DEBUG] How many trials should be performed? --> ").strip()
        trials = validatePosIntInput(trials)
                       
        for i in range(trials):
            #print(names, teams, end=' ') #was used for debugging
            retries_needed = 0
            main(names, weeks, debug_mode)
        print("MEAN:", mean(data))
        print("MAX:", max(data), "(count=", len([x for x in data if x==max(data)]), ")")
        print("MIN:", min(data), "(count=", len([x for x in data if x==min(data)]), ")")
        print("1 or 0 (count=", len([x for x in data if x==1 or x==0]), ")")
        again = input("Run again? [Y/N] --> ").strip()
        if again == 'Y': return True
        else: return False

    else: #standard execution, prints out schedules
        main(names, weeks, debug_mode)
        return False

    

def main(names, weeks, debug_mode):
    '''This function is responsible for determining how many full passes of the Scheduler will be needed
    to satisfy the given number of weeks. One full pass produces each team playing each other team once.'''
    global retries_needed
    global data
    random.seed()

    #initialize variables
    teams = list(map(Team, names))
    num_unique_matchups = len(teams)-1
    s = WeeklySchedule()

    num_passes = ceil(weeks / num_unique_matchups)
    retry = True

    #this loop handles dead ends and resets
    while retry:

        #this loop handles each full pass
        for i in range(num_passes):
            
            for team in teams: team.already_played_set = set() #reset already_played_sets

            if i < num_passes-1: #all but the last pass; a full pass is required
                retVal = runScheduler(teams, num_unique_matchups, s)
                if not retVal: break #if we failed, forget the rest of the loop and restart

            elif weeks % num_unique_matchups == 0: #last pass w/ enough weeks remaining for a full pass
                retVal = runScheduler(teams, num_unique_matchups, s)
                if retVal: retry = False
                
            else: #last pass w/ fewer weeks than unique matchups remaining
                retVal = runScheduler(teams, weeks % num_unique_matchups, s)
                if retVal: retry = False

        #out of the loop, if retVal is false, we have failed and must restart
        if not retVal:
            if not debug_mode: print("dead end, retrying")
            teams = list(map(Team, names))
            s = WeeklySchedule()
            retries_needed += 1


    #print(f"Retries Needed: {retries_needed}......Done")
    data.append(retries_needed) #used for debugging only

    if not debug_mode:
        print("\nSuccess:\n")
        s.printSchedule()
                
    

def runScheduler(teams, weeks, weekly_schedule):
    '''This function contains the core of the algorithm. It returns False if a dead end is reached'''
    num_teams = len(teams)
    iter_per_week = int(num_teams / 2)      #no. of matchups per week
    s = weekly_schedule

    try:
        #this loop goes week by week
        for w in range(weeks):

            #Tasks for starting a new week
            unscheduled_teams = teams[:]        #refresh unscheduled_teams
            scheduled_teams = []                #empty scheduled_teams
            s.schedule.append("")               #add a new index in the WeeklySchedule
            already_played_or_self_size = w+1   #this does not count any matchups that are made this week
                                                # (no. of teams) = already_played_or_self_size + yet_to_play_size


            #this loop goes matchup by matchup
            for i in range(iter_per_week):
                
                random.shuffle(unscheduled_teams)
                next_team = unscheduled_teams.pop()     #select a random team
                scheduled_teams.append(next_team)

                #determine first round of potential matches
                matches = [a for a in unscheduled_teams if a not in next_team.already_played_set]
                #debug_pre_matches = [b.name for b in matches] #used for readability while debugging

                if (len(unscheduled_teams) == 1):       #one team left means only one possible match
                    match = unscheduled_teams[0]        #we will not reach this point if the match is invalid...
                    #debug_matches = [match.name]

                else:                                   #...bc the list comp below would catch it first

                    #if there are too many teams left, a valid match for all remaining teams is guaranteed
                    if (len(unscheduled_teams)-1 <= already_played_or_self_size):
                        matches = [a for a in matches if testMatch(a, unscheduled_teams)] #otherwise, refine
                        
                        #'matches' now contains only matches that leave a valid match for all other teams
                        
                    #debug_matches = [b.name for b in matches] #used for readability while debugging

               
                    #is this the first matchup this week? If so, unique sets are assured and any match will do
                    if i == 0:
                        match = random.choice(matches)
                        
                    #if not, test for uniqueness
                    else:
                        matchFound = False
                        for k in range(len(matches)):
                            #construct sets for comparison
                            temp = matches[k]
                            set1 = next_team.already_played_set | set([temp])
                            set2 = temp.already_played_set | set([next_team])
                            #compare sets
                            if (setIsUnique(set1, scheduled_teams) and setIsUnique(set2, scheduled_teams)):
                                #...then this match is preferred
                                match = temp
                                matchFound = True
                                break #nothing differentiates preferred matches, so take the first we find

                        #if there are no preferred matches found...
                        if not (matchFound):
                            #print statements used for debugging:
                            #print(f"Forced to use non-unique set match in week {s.next_index} match {i} for team {next_team.name}")
                            #print(f"matches was: {debug_matches}  and  pre-matches was: {pre_matches}")
                            #print(f"Schedule thus far this week:\n{s.schedule[s.next_index]}")
                            #for t in teams: t.printSchedule()
                            match = random.choice(matches) #nothing differentiates non-preferred; pick a random one


                #Tasks once a match has been determined
                #debug_match = match.name #used for readability while debugging
                #debug_unsc_matches = [b.name for b in unscheduled_teams]
                unscheduled_teams.remove(match)
                scheduled_teams.append(match)
                setMatchForTeam(next_team, match)
                s.schedule[s.next_index] += next_team.name + " vs. " + match.name + "\n"

            #on matchup for loop complete, increment week of the WeeklySchedule:
            s.next_index += 1

        #on week for loop complete, report success:
        return True

    except IndexError: #catches all dead ends
        #print("INDEX ERROR")
        #print(f"Schedule thus far this week:\n{s.schedule[s.next_index]}")
        #for t in teams: t.printSchedule()
        return False
    
    
if __name__ == "__main__":
    metaWrapper()

    
