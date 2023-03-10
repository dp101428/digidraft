import requests
import random
import os
import json
import copy
from anyascii import anyascii

#url = "https://digimoncard.io/api-public/search.php?pack=BT-08: Booster New Awakening&series=Digimon Card Game"
#url = "https://digimoncard.io/api-public/getAllCards.php?sort=name&series=Digimon Card Game&sortdirection=asc"

#url = "https://digimoncard.io/api-public/search.php?series=Digimon Card Game&n=bearmon"

payload={}
headers = {}

# TODO:
# Enhance review of picks - inspect reviewing things, see digimon by colour and/or by level

#response = requests.request("GET", url, headers=headers, data=payload)
#print(response.text)
#print([x["cardrarity"]for x in response.json()])
#print(response.json())
#print(dir(response))
#print(headers)
#print(payload)
#initialiseDatabase("BT11")
#Store each pack checked this session
usedSets = {}
#Convert from short set names to long
conversionDict = {"BT11" : "BT-11: Booster Dimensional Phase", "BT10" : "BT-10: Booster Xros Encounter", "EX3" : "EX-03: Theme Booster Draconic Roar", "BT8" : "BT-08: Booster New Awakening"}
#pull rates: BT11 golds 1 per 2, omnimon 1/10 or 1/3, alphamon 1/3? (per case)
#BT11 4 campaign rare/box, 6 SR/box, 24 rares/box
#BT11 therefore has in its rare slots: 24 rares, 6 SRs, 4 campaigns, 1 secret, 1 secret/alt, 12 upshifted commons/uncommons

#Utility for going from set code to file
def genPath(setName):
	return "database/"+ setName[:2] +"/" + setName +".json"

#For use whenever the user gives input for selecting a digimon from a list
def interpretInput(options, inputChoice, allowDupes):
	if inputChoice in options:
		return inputChoice
	else:
		foundIndex = -1
		for i in range(len(options)):
			if options[i].find(inputChoice) == 0:
				if foundIndex == -1:
					foundIndex = i
					if(allowDupes):
						break
				else:
					foundIndex = -1
					print("Ambiguous input, try again")
					break
		if foundIndex == -1:
			return None
		else:
			return options[foundIndex]

#For printing the details for a card in a nice way, returning the formatted stuff as a string
def printCard(card):
	#returnString = card["name"] + "\n"
	#Dictionary for converting between card name categories and words
	conversionDict = {"name" : "Name: ", "type" : "Card Type: ", "color" : "Colour: ", "level" : "Level: ", "digi_type" : "Types: ", "play_cost" : "Cost: ", "evolution_cost" : "Evo Cost: ", "dp" : "DP: "
	, "maineffect" : "Effect: ", "soureeffect" : "Inherited Effect: ","cardnumber" : "Card ID: ", "cardrarity": "Rarity: "}
	#Dictionary to filter which entries get printed based on card type
	typeFilterDict = {"Digimon": conversionDict.keys(), "Digi-Egg": ["name", "type", "color", "level", "digi_type", "soureeffect", "cardnumber", "cardrarity"], 
		"Option" : ["name", "type", "color", "digi_type", "play_cost", "maineffect", "soureeffect", "cardnumber","cardrarity"],
		"Tamer": ["name", "type", "color", "digi_type" , "play_cost", "maineffect", "soureeffect", "cardnumber","cardrarity"]}
	#Grab the type once because it's annoying doing it repeatedly
	cardType = card["type"]
	#easy way?
	returnString = ""
	for key, value in card.items():
		if key in typeFilterDict[cardType]:
			#Special-case security effects
			if key == "soureeffect" and (cardType == "Option" or (cardType == "Tamer" and "Security" not in card["maineffect"])):
				returnString += "Security Effect: " + str(value) + "\n"
			elif key == "digi_type":
				returnString += str(conversionDict[key]) + str(value)+ " " + str(card["attribute"]) + "\n"
			elif key == "evolution_cost":
				returnString += str(conversionDict[key]) + str(value[0]["cost"]) +" from a level " + str(value[0]["level"]) + " " + value[0]["colour"] + (" digimon" if card["level"] != 3 else " digi-egg") + ("\n" if len(value) == 1 else ", or " + str(value[1]["cost"]) +" from a level " + str(value[1]["level"]) + " " + value[1]["colour"] + (" digimon" if card["level"] != 3 else " digi-egg") + "\n")
			elif key == "color":
				returnString += str(conversionDict[key]) + str(value) + ("\n" if card["colour2"] == None else " "+ card["colour2"] + "\n")
			else:
				returnString += str(conversionDict[key]) + str(value) + "\n"
	return returnString

#Used after changing stuff in a set
def replaceFile(file, jsonObject):
	file.seek(0)
	file.truncate(0)
	json.dump(jsonObject, file)

#find index of card by name with list of card objects
def findCardIndex(card, grouping):
	return [checkedCard["name"] for checkedCard in grouping].index(card)

with open("database/BT/BT8.json", "r+") as f:
	data = json.load(f)
	#print(data["Super Rare"][-1])
	#data["Super Rare"][-1]["evolution_cost"][0]["colour"] = "Any"
	#rarities = set([card["cardrarity"] for card in data])
	#print(rarities)
	#print([card for card in data["Uncommon"] if "Cavalier" in card["name"]])
	#for rarity, group in data.items():
	#	print(rarity)
	#	print(len(group))
	#data["Rare"].append(data["Common"].pop(findCardIndex("Biyomon", data["Common"])))
	#print([card["name"] for card in data["Common"]])
	#print([card["name"] for card in data["Rare"]])
	#for rarity, cardset in data.items():
	#	print(rarity)
	#	print(cardset[0])
	#	print([card["name"] for card in data[rarity] if "AA" in card["name"]])
	#print(data["Gold Rare"])
	#print([card["name"] for card in data["Super Rare"] if "AA" in card["name"]])
	#print([card["name"] for card in data["Super Rare"]])
	#print(data["Rare"])
	#lost = [card for card in data["Super Rare"] if "AA" in card["name"]]
	#for card in lost:
	#	card["cardrarity"] = "Alternative Art"
	#data["Alternative Art"] += lost
	#print([card["name"] for card in data["Alternative Art"]])
	#correctedGroup = [card["name"] for card in data["Super Rare"] if "AA" not in card["name"]]
	#print(correctedGroup)
	#data["Super Rare"] = correctedGroup
	#replaceFile(f, data)
	#print([card for card in data["Uncommon"] if "Veemon" in card["name"]])


#Tired of cards ending up out of order
def sortSet(cardSet):
	with open(genPath(cardSet), "r+") as f:
		data = json.load(f)
		for category, group in data.items():
			if category == "All":
				continue
			group.sort(key = lambda card: card["cardnumber"][-3:])
			print([card["name"] +" " +card["cardnumber"] + " " + card["cardnumber"][-3:] for card in group])
		replaceFile(f, data)


#Function in case AA cards wind up not in AA rarity
def moveAA(cardSet):
	with open(genPath(cardSet), "r+") as f:
		data = json.load(f)
		for category, group in data.items():
			if category != "Alternative Art" and category != "All":
				print(category)
				print([card["name"] for card in group])
				movedCards = [card for card in group if "AA" in card["name"]]
				group[:] = [card for card in group if "AA" not in card["name"]]
				print([card["name"] for card in group])
				print([card["name"] for card in movedCards])
				data["Alternative Art"] += movedCards
				print([card["name"] for card in data["Alternative Art"]])
		replaceFile(f, data)
	sortSet(cardSet)

def getCard(cardName, data):
	for rarity in data.values():
		if cardName in [card["name"] for card in rarity]:
			for card in rarity:
				if card["name"] == cardName:
					return card

#Utility for editing rarities
def editRarities(cardSet):
	with open(genPath(cardSet), "r+") as f:
		data = json.load(f)
		for card in data:
			if card["cardrarity"] == "not yet set":
				print("Rarity not set: " + card["name"] + " " + card["cardnumber"] + ". Enter the correct rarity")
				newRarity = input()
				card["cardrarity"] = newRarity
		replaceFile(f, data)

#For adding all standard-ish evo requirements
def setEvoRequirements(cardSet):
	with open(genPath(cardSet), "r+") as f:
		data = json.load(f)
		for rarity, group in data.items():
			ending = False
			if rarity != "All":
				print(rarity)
				for card in group:
					if card["type"] == "Digimon":
						#Checking if pre-correction
						if (isinstance(card["evolution_cost"], int)):
							#Assume that initial evolution cost is from lower level of primary colour
							standardEvoCost = card["evolution_cost"]
							#This is how we'll output later
							#print("From " + card["color"] + " level " + str(card["level"]-1) + " for " + str(standardEvoCost))
							card["evolution_cost"] = [{"colour" : card["color"], "level": card["level"] -1, "cost": standardEvoCost}]
							print("Card: " + card["name"] + ". Colour: " + card["color"] + ("" if card["colour2"] == None else " " + card["colour2"]) + 
								". Evo from " + card["color"] + " level " + str(card["level"]-1) + " for " + str(standardEvoCost) +". Is there a second evolution? y if so. Otherwise return")
							bypass = input()
							if bypass == "y":
								newEvo = {}
								print("What is the 2nd evolution colour? Leave it blank to select either its own colour if mono-coloured or the second colour if multi-colour")
								newColour = input()
								if newColour != "":
									newEvo["colour"] = newColour
								else:
									newEvo["colour"] = card["color"] if card["colour2"] == None else card["colour2"]
								print("What is the 2nd evolution level? Leave it blank to select the same as the first level")
								newLevel = input()
								if newLevel != "":
									newEvo["level"] = int(newLevel)
								else:
									newEvo["level"] = card["evolution_cost"][0]["level"]
								print("What is the 2nd evolution cost? Leave it blank to set it as the same as the first")
								newCost = input()
								if newCost != "":
									newEvo["cost"] = int(newCost)
								else:
									newEvo["cost"] = card["evolution_cost"][0]["cost"]
								card["evolution_cost"].append(newEvo)
							elif bypass == "End":
								ending = True
								break
			if ending:
				break
		replaceFile(f, data)


#Special evolutions and DNA
def addSpecialEvo(cardSet):
	with open(genPath(cardSet), "r+") as f:
			data = json.load(f)
			for rarity, group in data.items():
				ending = False
				if rarity != "All":
					print(rarity)
					for card in group:
						if card["type"] == "Digimon":
							#Helping narrow down which we have to look at
							if "X Antibody" in card["name"] or (rarity != "Common" and (card["stage"] == "Armor Form" or rarity != "Uncommon")):
								print("Card: " + card["name"] +". Does this card have alternative evolutions? y if so")
								check = input()
								if check == "y":
									print("Type the name of a card, or DNA if the special evolution is from that, or Contain and then the name if that's the format")
									varityInput = input()
									if varityInput == "DNA":
										newText = "<DNA Digivolution: 0 from "+card["evolution_cost"][0]["colour"]+" Lv"+ str(card["level"]-1)+ " + " +(card["evolution_cost"][0]["colour"] if len(card["evolution_cost"]) == 1 else card["evolution_cost"][1]["colour"])+" Lv"+str(card["level"]-1)+"> " + card["maineffect"]
										card["maineffect"] = newText
										print(newText)
									elif "Contain" in varityInput:
										newText = "Digivolve: " + altCost + " if name contains ["+ varityInput[8:]+"] " + card["maineffect"]
										card["maineffect"] = newText
										print(newText)
									else:
										print("How much is the alternative cost?")
										altCost = input()
										newText = "Digivolve: " + altCost + " from ["+ varityInput+"] " + card["maineffect"]
										card["maineffect"] = newText
										print(newText)
			replaceFile(f, data)


def packInitialised(set):
    return(os.path.exists("database/"+ set[:2] +"/" + set +".json"))
def genPack(set):
	#Start out by adding the set to the dictionary if it's not in there yet
	#if set not in usedSets.keys():
	#		usedSets[set] = {"full" : requests.request("GET", "https://digimoncard.io/api-public/search.php?series=Digimon Card Game&pack=" + conversionDict[set], headers=headers, data=payload).json}
	#		#usedSets[set]["commons"] = 
	#initialiseDatabase(set)
	#every pack has 12 cards
	#7 commons 3 uncommons 1 rare 1 other

	pack = []
	if not packInitialised(set):
		print("Invalid path")
		return
	with open(genPath(set)) as f:
		initialData = json.load(f)
		#Really need to just hand off full card objects
		pack += [card for card in random.sample(initialData["Common"], 7)]
		pack += [card for card in random.sample(initialData["Uncommon"], 3)]
		#To ensure ordering is correct, need to generate the 2 possible rares first and then place after
		potentialRares = [card for card in random.sample(initialData["Rare"], 2)]
		#BT11 commmon/uncommon upshift replaces first rare so check here
		#Seems that 50% of packs have commons/uncommons
		if set == "BT11" and random.random() < 1/2:
			#commons/uncommons seem equally commonly upshifted
			if random.random() < 1/2:
				pack += [card for card in random.sample(initialData["Common"], 1)]
			else:
				pack += [card for card in random.sample(initialData["Uncommon"], 1)]
		else:
			pack += [potentialRares[0]]
		#Check for all the ways of being a hit
		#Ghost/gold rare moment first
		#Assuming 1/10 and 1/2 cases probability
		if ((set == "BT10" or set == "BT6") and random.random() < 1/10/12/24) or set == "BT11" and random.random() < 1/2/12/24:
			if set == "BT11":
				pack += [card for card in random.sample(initialData["Gold Rare"], 1)]
			else:
				pack += [card for card in random.sample(initialData["Ghost Rare"], 1)]
		#Really easy for non-BT11, 8 hits (6 sr 1 sec 1 alt) per box so 1/3 packs
		elif set != "BT11" and random.random() < 1/3:
			#3/4 chance at this stage of super
			if random.random() < 3/4:
				pack += [card for card in random.sample(initialData["Super Rare"], 1)]
			#50/50 as to sec
			elif random.random() < 1/2:
				pack += [card for card in random.sample(initialData["Secret Rare"], 1)]
			#Otherwise alt art
			else:
				pack += [card for card in random.sample(initialData["Alternative Art"], 1)]

		#BT11-shaped suffering
		elif set == "BT11" and random.random() <= .5:
			#4/12 = 1/3 campaign
			if random.random() < 1/3:
				pack += [card for card in random.sample(initialData["Campaign Rare"], 1)]
			#6/8 = 3/4 SR
			elif random.random() < 3/4:
				pack += [card for card in random.sample(initialData["Super Rare"], 1)]
			#50/50 as to sec
			elif random.random() < 1/2:
				pack += [card for card in random.sample(initialData["Secret Rare"], 1)]
			#Otherwise alt art
			else:
				pack += [card for card in random.sample(initialData["Alternative Art"], 1)]
		#pack the rest with rares
		if(len(pack) < 12):
			pack += [potentialRares[1]]
		#print([card for card in pack])

	return pack


def initialiseDatabase(cardSet):
	#First make sure that category of sets exists
	if not os.path.exists("database/" + cardSet[:2]):
		os.mkdir("database/" + cardSet[:2])
	#Then make the set itself
	if not packInitialised(cardSet):
		with open(genPath(cardSet), "w") as f:
			url = "https://digimoncard.io/api-public/search.php?pack=" +  conversionDict[cardSet] + "&series=Digimon Card Game"
			responsej = requests.request("GET", url, headers=headers, data=payload).json()
			json.dump(responsej, f)

#I hate it here
def fixColours(cardSet):
	with open(genPath(cardSet), "r+") as f:
		initialData = json.load(f)
		for rarity, cards in initialData.items():
			print(rarity)
			cancel = False
			for card in cards:
				print("Card: " + card["name"] + ". Colour: " + card["color"] + ". If the card has a second colour, type it, otherwise type Skip")
				newColour = input()
				if newColour != "Skip" and newColour != "":
					card["colour2"] = newColour
				else:
					card["colour2"] = None
				if newColour == "End":
					cancel = True
					break
			if cancel:
				break
		#print(initialData["Rare"][1])
		replaceFile(f, initialData)
#Easily duplicate AA entries
def dupeAA(cardSet):
	if not(packInitialised(cardSet)):
		return
	with open(genPath(cardSet), "r+") as f:
		initialData = json.load(f)
		#Unfortunately, list comprehension is not quite powerful enough
		newData = []
		for entry in initialData:
			if entry["card_sets"].count(conversionDict[cardSet]) > 1:
				actEntry = copy.deepcopy(entry)
				newData.append(actEntry)
				actEntry["name"] += " AA"
				actEntry["card_sets"] = [conversionDict[cardSet]]
				entry["card_sets"].remove(conversionDict[cardSet])
				if entry["cardrarity"] == "Alternative Art":
					entry["cardrarity"] = "not yet set"
				actEntry["cardrarity"] == "Alternative Art"
		initialData += newData
		f.seek(0)
		json.dump(initialData, f)

#This is for after the database has been sanitised
def sortDatabase(cardSet):
	if not packInitialised(cardSet):
		return
	with open("database/"+ cardSet[:2] +"/" + cardSet +".json", "r+") as f:
		initialData = json.load(f)
		#Get a list of all rarities in the set
		rarities = [*set([x["cardrarity"] for x in initialData])]
		print(rarities)
		sortedData = {rarity : ([y for y in initialData if y["cardrarity"] == rarity]) for rarity in rarities}
		sortedData["All"] = initialData
		replaceFile(f, sortedData)

#actually draft
def draft(set, box, playerCount, test, solo):
	if not packInitialised(set):
		return
	data = {}
	with open("database/"+ set[:2] +"/" + set +".json") as f:
		data = json.load(f)
	#Going to try 6 drafters, 4/pack, but any factor of 24 works
	if 24%playerCount != 0:
		print("Invalid player count")
		return
	packsToDraft = []
	if not box:
		for i in range(playerCount):
			packsToDraft.append([])
			for j in range(int(24/playerCount)):
				packsToDraft[i].append(genPack(set))
	picks = []
	for pack in packsToDraft:
		picks.append([])
	currentPlayer = 0
	currentPack = 0
	pickNumber = 0
	while currentPack < 24/playerCount:
		#print("Make your next pick by typing a card name (or enough to identify it), or input Review to see past picks, or Inspect and then a card name to see details")
		#Get the pack in a variable so we don't have to keep fetching it
		pack = packsToDraft[(currentPlayer + pickNumber)%playerCount][currentPack]
		print([card["name"] for card in pack])
		choice = None
		goingForward = True
		if test or (solo and currentPlayer != 0):
			choice = pack[int(random.random() * len(pack))]["name"]
		while choice is None:
			print("Make your next pick by typing a card name (or enough to identify it), or input Review to see past picks, or Inspect and then a card name to see details. Your options:")
			print([card["name"] for card in pack])
			playerInput = input()
			if playerInput == "Review":
				print([pick["name"] for pick in picks[currentPlayer]])
				print("To inspect a card more closely, use Inspect and a card name. To see levels, type Levels, and for the colours of your digimon, Colours. For by-level by-colour, type Spread")
				newInput = input()
				while newInput != "Return":
					if "Inspect" in newInput:
						inspectedCard = interpretInput([card["name"] for card in picks[currentPlayer]], newInput[8:], True)
						if inspectedCard:
							print(printCard(picks[currentPlayer][[card["name"] for card in picks[currentPlayer]].index(inspectedCard)]))
					elif newInput == "Levels":
						#If I didn't care about sorting the output I could just pull the categories from the cards, but..
						cardCategories = {"Digi-Egg": 0, "Rookie": 0, "Champion": 0, "Ultimate": 0, "Mega": 0, "Tamer": 0, "Option" : 0}
						for card in picks[currentPlayer]:
							if card["type"] == "Digimon":
								cardCategories[card["stage"]] += 1
							else:
								cardCategories[card["type"]] += 1
						for category, count in cardCategories.items():
							print(category + ": " + str(count))
					elif newInput == "Colours":
						#multicolour fun
						print("Values in parenthesis exclude multi-colour cards (which count as both colours otherwise). First set of results are digimon, 2nd is for options listing the count per requirement")
						#First number is total 2nd is mono
						colourCounts = {"Red": [0,0], "Blue": [0,0], "Yellow": [0,0], "Green": [0,0], "Black": [0,0],"Purple": [0,0], "White": [0,0]}
						optionRequirementCounts = {}
						for card in picks[currentPlayer]:
							if card["type"] == "Digimon":
								colourCounts[card["color"]][0] += 1
								if card["colour2"] != None:
									colourCounts[card["colour2"]][0] += 1
								else:
									colourCounts[card["color"]][1]
							if card["type"] == "Option":
								if card["colour2"] == None:
									colourReq = card["color"]
								else:
									#Sort the colour pair to count all equally
									colourReq = [card["color"], card["colour2"]]
									colourReq.sort()

								if colourReq in optionRequirementCounts.keys():
									optionRequirementCounts[colourReq] += 1
								else:
									optionRequirementCounts[colourReq] = 1
						print("Digimon:")
						for colour, counts in colourCounts.items():
							print(colour + ": "+ str(counts[0])+", (" + str(counts[1]) + ")")
						print("Options:")
						for colour, count in optionRequirementCounts.items():
							print(colour + ": " + str(count))
					print("To inspect a card more closely, use Inspect and a card name. To see levels, type Levels, and for the colours of your digimon, Colours. For by-level by-colour, type Spread")
					newInput = input()
			elif "Inspect" in playerInput:
				inspectedCard = interpretInput([card["name"] for card in pack], playerInput[8:], False)
				if inspectedCard:
					print(printCard(pack[[card["name"] for card in pack].index(inspectedCard)]))
			else:
				attemptedPick = interpretInput([card["name"] for card in pack], playerInput, False)
				if attemptedPick != None:
					choice = attemptedPick
		#print(choice)
		picks[currentPlayer].append(pack.pop([card["name"] for card in pack].index(choice)))
		if(goingForward):
			currentPlayer += 1
			if currentPlayer == playerCount:
				currentPlayer = 0
				pickNumber += 1
			if currentPlayer == 0 and len(packsToDraft[0][currentPack]) == 0:
				currentPack += 1
				pickNumber = 0
				goingForward = False
		else:
			currentPlayer -= 1
			#Annoying how it's not symmetrical
			if currentPlayer < 0:
				currentPlayer = playerCount-1
			if(currentPlayer == 1):
				pickNumber += 1
			if currentPlayer == 0 and len(packsToDraft[0][currentPack]) == 0:
				currentPack += 1
				pickNumber = 0
				goingForward = True

	exportChoice = input("Do you want to export the drafted decks to import to a deckbuilder?")
	if exportChoice == "Yes" or exportChoice == "y":
		with open("latest draft.txt", "w", encoding="utf-8") as f:
			for choices in picks:
				#Main thing we have to do is shrink duplicates
				i = 0
				#this is way faster if we sort it
				choices.sort(key = lambda card: card["cardnumber"][-3:])
				#cardCodeConversion = {card : getCard(card, data)["cardnumber"] for card in choices}
				print([card["cardnumber"] for card in choices])
				while i < len(choices):
					curCard = choices[i]
					cardCode = curCard["cardnumber"]
					numCopies = 1
					j = i + 1
					#need to deal with remote possibility of cards from other sets sharing the sorting part of the code
					while j < len(choices) and choices[j]["cardnumber"][-3:] == cardCode[-3:]:
						if choices[j]["cardnumber"] == cardCode:
							choices.pop(j)
							numCopies += 1
						else:
							j += 1
					cardName = curCard["name"] if "AA" not in curCard["name"] else curCard["name"][:-3]
					#print(str(numCopies) + " " + cardName + " " + cardCode + "\n")
					f.write(anyascii(str(numCopies) + " " + cardName + " " + cardCode) + "\n")
					i += 1
				f.write("\n")

draft("BT8", False, 6, False, True)
#addSpecialEvo("BT8")
#sortSet("BT8")