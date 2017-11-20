import Tasks

def loadAllLists(taskList):
	changeList = []
	changeList = taskList.loadAllTasks()
	changeList += taskList.loadWeeklyTasks()
	changeList += taskList.loadDailyTasks()
	return changeList
	
	
def refreshAllLists(taskList):
	listsUpdated ={}
	listsUpdated['Weekly'] = taskList.regenerateWeeklyTasks()
	listsUpdated['Daily'] = taskList.regenerateDailyTasks()
	return listsUpdated

def printAllLists(taskList):
	taskList.writeToTextAllTasks()
	taskList.writeToTextWeeklyTasks()
	taskList.writeToTextDailyTasks()
	
def main():
	taskList = Tasks.TaskList()
	changeList = loadAllLists(taskList)
	taskList.updateToCurrentTime()
	taskList.createProgressAndNotesInfra()
	taskList.updateTasks(changeList)
	listsUpdated = refreshAllLists(taskList)
	taskList.logAllUpdates(changeList)
	printAllLists(taskList)
	taskList.printAllListsToHTML()
	for changes in changeList:
		print(changes)
	print('Main Exited')
	
if __name__== "__main__":
  main()