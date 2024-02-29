import requests
import random
import os
import json
import copy
from anyascii import anyascii

#List of functions:
#genPath(setName) - used to go from set code (BT11) to file structure path
#interpretInput(options, inputChoice, allowDupes) - used when repeatedly taking input (inputChoice) to pick a string from a list of strings (options) and can optionally fail if 2+ values are equally appropriate
#printCard(card) - turns a card object into a nicely-formatted string
#replacefile(file, json) - takes a filepath and a json object, replaces the file with the contents of the json
#packInitialised(cardSet) - checks to see if a certain set exists
#openSet(cardSet) - checks to see if a set is already opened, if so it returns that instance of it, otherwise it opens the set and adds it to the list of set instances, then returns it
#findCardIndex(card, grouping) - finds the index of a card from the name of the string within the given list
#sortSet(cardSet) - sorts every card group by card number
#raritySort(cardSet) - moves cards from their existing rarities to the rarity listed in their object
#deUnknown(cardSet) - functions like raritySort except only removes things from unknown rarity
#moveAA(cardSet) - like rarity sort except moves any card with AA in its name to AA
#getCard(cardname, data) - fetches a card from a json object, by name
#getCardFromCode(cardCode, data) - gets a card from its card ID, if data is not given looks in the set corresponding to the card ID
#editRarities(cardset) - takes a set that is not yet split into rarities and manually edits the rarity of any card whose rarity is listed as "not yet set"
#setEvoRequirements(cardSet) - allows for the setting of all regular evo requirements, necessary for cards that can evo from multiple colours
#addspecialevo(cardset) - used for manually editing every card to add any "special" digivolution requirements, basically anything that goes in a grey box before the effect, and prepends the condition to the card's regular text
#genPack(cardSet, cube, custom, originalSet) - generates a pack from a set. If cube is true, assumes only 1 rarity, if custom is true then cardSet is data, otherwise it's a string naming a set. OriginalSet is a copy of cardSet to facilitate drawing without replacement from a cube that lacks the cards for the number of players drafting
#initialiseDatabase(cardSet, override) - goes and downloads whatever set you tell it to using digimoncard.io's API, with override doing even if the file is already made
#fixColours(cardSet) - used for manually adding a second colour to cards, ideally used before the evolution-modifying functions
#dupeAA(cardSet) - takes every card that is listed as showing up in the set twice (which is every AA card) and makes a duplicate of it, gives one a rarity of AA and the other as "not yet set" if prior rarity was unknown. used on unsorted set
#sortDatabase(cardSet) - takes an unsorted set and sorts the cards by rarity, with the unsorted set remaining under "all"
#detectDuplicate(draftSet, cube) finds all duplicate cards in the set
#draft(draftSet, box, playerCount, test, solo, numpacks, custom, cube) - starts a draft, first argument defines the set, second determines if all packs are considered to be coming from one "box" (so fixed SR ratios), then number of players, test makes every player pick randomly, solo makes all but one player pick randomly, numpacks is how many packs to use, custom if it's a custom set, cube if the custom set has flat rarities
#customSet - used for creating a custom set, whether by merging together various existing sets, adding or removing cards from them, making something entirely new, cube or not cube, input by file or console.
#unpackSet - turns an exported custom set into a json for drafting
#menu - provides access to the above three functions
#url = "https://digimoncard.io/api-public/search.php?pack=BT-08: Booster New Awakening&series=Digimon Card Game"
#url = "https://digimoncard.io/api-public/getAllCards.php?sort=name&series=Digimon Card Game&sortdirection=asc"

#url = "https://digimoncard.io/api-public/search.php?series=Digimon Card Game&n=bearmon"

payload={}
headers = {}



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
conversionDict = {"BT11" : "BT-11: Booster Dimensional Phase", "BT10" : "BT-10: Booster Xros Encounter", "EX3" : "EX-03: Theme Booster Draconic Roar", "BT8" : "BT-08: Booster New Awakening", "BT12": "BT-12: Booster Across Time",  "EX4": "EX-04: Theme Booster Alternative Being"}
#pull rates: BT11 golds 1 per 2, omnimon 1/10 or 1/3, alphamon 1/3? (per case)
#BT11 4 campaign rare/box, 6 SR/box, 24 rares/box
#BT11 therefore has in its rare slots: 24 rares, 6 SRs, 4 campaigns, 1 secret, 1 secret/alt, 12 upshifted commons/uncommons

#Utility for going from set code to file
def genPath(setName):
	return "database/"+ setName[:2] +"/" + setName +".json"

#For use whenever the user gives input for selecting a digimon from a list
def interpretInput(options, inputChoice, allowDupes):
	if inputChoice.upper() in (option.upper for option in options):
		return inputChoice
	else:
		foundIndex = -1
		for i in range(len(options)):
			if options[i].upper().find(inputChoice.upper()) == 0:
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
				returnString += str(conversionDict[key])
				for cost in value:
					if cost != value[0]:
						returnString += ", "
						if cost == value[-1]:
							returnString += "or "
					returnString += str(cost["cost"]) +" from a level " + str(cost["level"]) + " " + cost["colour"] + (" digimon" if card["level"] != 3 else " digi-egg")
				returnString += "\n"
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

def packInitialised(cardSet):
    return(os.path.exists(genPath(cardSet)))

#For either fetching set if already opened or opening it
def openSet(setName):
	if setName in usedSets.keys():
		return usedSets[setName]
	else:
		if packInitialised(setName):
			with open(genPath(setName), "r+") as f:
				data = json.load(f)
				usedSets[setName] = data
				return data

#find index of card by name with list of card objects
def findCardIndex(card, grouping):
	return [checkedCard["name"] for checkedCard in grouping].index(card)


with open("database/EX/EX4.json", "r+") as f:
	data = json.load(f)
	#print(data["Super Rare"][3])
	#print([card for card in data["Uncommon"] if "Cavalier" in card["name"]])
	#for rarity, group in data.items():
	#	print(rarity)
	#data["Uncommon"].append(data["Super Rare"].pop([card["name"] for card in data["Super Rare"]].index("RizeGreymon")))
	#print(data["Uncommon"][-1])
	#data["Uncommon"][-1]["cardrarity"] = "Uncommon"
	#for rarity, cardset in data.items():
	#	print(rarity)
	#	print(len(cardset))
	#	print([card["name"] for card in data[rarity]])
	
	#data["Uncommon"][:] = [card for card in data["Uncommon"] if not "AA" in card["name"]]
	#print([card["name"] for card in data["Uncommon"]])
	#print(len(data["Uncommon"]))
	#lost = [card for card in data["Super Rare"] if "AA" in card["name"]]
	#for card in lost:
	#	card["cardrarity"] = "Alternative Art"
	#data["Alternative Art"] += lost
	#print([card["name"] for card in data["Alternative Art"]])
	#correctedGroup = [card["name"] for card in data["Super Rare"] if "AA" not in card["name"]]
	#print(correctedGroup)
	#data["Super Rare"] = correctedGroup
	#replaceFile(f, data)

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

#Goes through each rarity and puts the cards from it in the correct one
def raritySort(cardSet):
	with open(genPath(cardSet), "r+") as f:
		data = json.load(f)
		for rarity, group in data.items():
			if rarity == "All":
				continue
			print(rarity)
			unfitCards = [card for card in group if card["cardrarity"] != rarity]
			if len(unfitCards) == 0:
				continue
			print([card["name"] for card in unfitCards])
			print([card["cardrarity"] for card in unfitCards])
			group[:] = [card for card in group if card["cardrarity"] == rarity]
			print([card["name"] for card in group])
			if all([card["cardrarity"] == unfitCards[0]["cardrarity"] for card in unfitCards]):
				data[unfitCards[0]["cardrarity"]] += unfitCards
			else:
				print("panic")
		replaceFile(f, data)
	sortSet(cardSet)
#Get cards out of Unknown rarity
def deunknown(cardSet):
	with open(genPath(cardSet), "r+") as f:
		data = json.load(f)
		#Make sure the number of rarities is the same, to only actually replace if we didn't make more
		oldrarities = len(data.keys())
		for card in data["Unknown"]:
			print("Rarity unknown: " + card["name"] + " " + card["cardnumber"] + ". Enter the correct rarity")
			newRarity = input()
			if newRarity == "Ghost Rare":
				data["Ghost Rare"] = [] 
			card["cardrarity"] = newRarity
			data[card["cardrarity"]].append(card)
		print(data.keys())
		if len(data.keys()) == oldrarities + 1:
			print("All clear")
			del data["Unknown"]
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

#Getting card from name
def getCard(cardName, data):
	for rarity in data.values():
		if cardName in [card["name"] for card in rarity]:
			for card in rarity:
				if card["name"] == cardName:
					return card
#Getting card from a code
def getCardFromCode(cardCode, data = None):
	if data == None:
		cardSet = cardCode.split("-")[0]
		if cardSet in usedSets.keys():
			data = usedSets[cardSet]
		else:
			if packInitialised(cardSet):
				with open(genPath(cardSet), "r+") as f:
					data = json.load(f)
					usedSets[cardSet] = data
	for rarity, cards in data.items():
		if rarity != "Alternative Art":
			if cardCode in [card["cardnumber"] for card in cards]:
				return cards[[card["cardnumber"] for card in cards].index(cardCode)]
	return None
#Utility for editing rarities
def editRarities(cardSet):
	with open(genPath(cardSet), "r+") as f:
		data = json.load(f)
		for card in data:
			if card["cardrarity"] == "not yet set" or card["cardrarity"] == "Unknown":
				print("Rarity not set or unknown: " + card["name"] + " " + card["cardnumber"] + ". Enter the correct rarity")
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
							print("Card: " + card["name"] +". Does this card have alternative evolutions? y if so")
							print(card["maineffect"])
							check = input()
							if check == "y":
								print("Type the name of a card, or DNA if the special evolution is from that, or Contain and then the name if that's the format, or Save if generic Save evo")
								varityInput = input()
								if varityInput == "DNA":
									newText = "<DNA Digivolution: 0 from "+card["evolution_cost"][0]["colour"]+" Lv"+ str(card["level"]-1)+ " + " +(card["evolution_cost"][0]["colour"] if len(card["evolution_cost"]) == 1 else card["evolution_cost"][1]["colour"])+" Lv"+str(card["level"]-1)+"> " + (card["maineffect"] or "")
									card["maineffect"] = newText
									print(newText)
								elif varityInput == "Save":
									newText = "Digivolve: " + str(card["evolution_cost"][0]["cost"]) + " from Lv." + str(card["level"]-1) + " w/<Save> in text " + (card["maineffect"] or "")
									card["maineffect"] = newText
									print(newText)
								elif "Contain" in varityInput:
									newText = "Digivolve: " + altCost + " if name contains ["+ varityInput[8:]+"] " + (card["maineffect"] or "")
									card["maineffect"] = newText
									print(newText)
								else:
									print("How much is the alternative cost?")
									altCost = input()
									newText = "Digivolve: " + altCost + " from "+ varityInput+" " + (card["maineffect"] or "")
									card["maineffect"] = newText
									print(newText)
			replaceFile(f, data)



def genPack(cardSet, cube, custom, originalSet):
	#Start out by adding the set to the dictionary if it's not in there yet
	#if set not in usedSets.keys():
	#		usedSets[set] = {"full" : requests.request("GET", "https://digimoncard.io/api-public/search.php?series=Digimon Card Game&pack=" + conversionDict[set], headers=headers, data=payload).json}
	#		#usedSets[set]["commons"] = 
	#initialiseDatabase(set)
	#every pack has 12 cards
	#7 commons 3 uncommons 1 rare 1 other
	pack = []
	if cube:
		#Assuming true cube fashion where the picked cards are removed
		if len(cardSet) < 12:
			pack += cardSet
			cardSet = originalSet.copy()
			pack += random.sample(cardSet, 12-len(pack))
		else:
			pack += random.sample(cardSet, 12)
		cardSet[:] = [card for card in cardSet if card not in pack]
		return pack
	#Hitrate determined by rarities present + which set
	hitrate = 0
	#If custom then it's simple - 7 SRs (technically varies between sets but we'll say 7), 1 sec 1 AA if those categories exist
	if custom:
		hitrate = 7 + (1 if "Secret Rare" in cardSet.keys() else 0) + (1 if "Alternative Art" in cardSet.keys() else 0)
	else:
		hitrate = 9
	initialData = cardSet
	#Really need to just hand off full card objects
	pack += [card for card in random.sample(initialData["Common"], 7)]
	pack += [card for card in random.sample(initialData["Uncommon"], 3)]
	#To ensure ordering is correct, need to generate the 2 possible rares first and then place after
	potentialRares = [card for card in random.sample(initialData["Rare"], 2)]
	#BT11 commmon/uncommon upshift replaces first rare so check here
	#Seems that 50% of packs have commons/uncommons
	if cardSet == "BT11" and random.random() < 1/2:
		#commons/uncommons seem equally commonly upshifted
		if random.random() < 1/2:
			pack.append(random.choice(initialData["Common"], 1))
		else:
			pack.append(random.choice(initialData["Uncommon"], 1))
	else:
		pack += [potentialRares[0]]
	#Check for all the ways of being a hit
	#Ghost/gold rare moment first
	#Assuming 1/10 and 1/2 cases probability
	if ((cardSet == "BT10" or cardSet == "BT6" or cardSet == "BT12") and random.random() < 1/10/12/24) or cardSet == "BT11" and random.random() < 1/2/12/24:
		if cardSet == "BT11":
			pack += [card for card in random.sample(initialData["Gold Rare"], 1)]
		else:
			pack += [card for card in random.sample(initialData["Ghost Rare"], 1)]
	#Use prior hitrate (8 or 9 packs per box depending on set)
	elif cardSet != "BT11" and random.random() < hitrate/24:
		#7/9 chance at this stage of super
		if random.random() < 7/hitrate:
			pack += [card for card in random.sample(initialData["Super Rare"], 1)]
		#50/50 as to sec
		elif random.random() < 1/2:
			pack += [card for card in random.sample(initialData["Secret Rare"], 1)]
		#Otherwise alt art
		else:
			pack += [card for card in random.sample(initialData["Alternative Art"], 1)]
	#BT11-shaped suffering
	elif cardSet == "BT11" and random.random() <= .5:
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


def initialiseDatabase(cardSet, override = False):
	#First make sure that category of sets exists
	if not os.path.exists("database/" + cardSet[:2]):
		os.mkdir("database/" + cardSet[:2])
	#Then make the set itself
	if override or not packInitialised(cardSet):
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
				actEntry["cardrarity"] = "Alternative Art"
		initialData += newData
		replaceFile(f, initialData)

#This is for after the database has been sanitised
def sortDatabase(cardSet):
	if not packInitialised(cardSet):
		return
	with open(genPath(cardSet), "r+") as f:
		initialData = json.load(f)
		#Get a list of all rarities in the set
		rarities = [*set([x["cardrarity"] for x in initialData])]
		print(rarities)
		sortedData = {rarity : ([y for y in initialData if y["cardrarity"] == rarity]) for rarity in rarities}
		sortedData["All"] = initialData
		replaceFile(f, sortedData)
#For noting which cards have duplicates to disambiguate display
#Takes a dictionary or list
def detectDuplicate(cardSet, cube):
	dupedCards = set()
	if cube:
		for i in range(len(cardSet)):
			if cardSet[i]["cardnumber"] in dupedCards:
				continue
			for j in range(i+1, len(cardSet)):
				if cardSet[i]["name"] == cardSet[j]["name"]:
					dupedCards.add(cardSet[i]["cardnumber"])
					dupedCards.add(cardSet[j]["cardnumber"])
	else:
		tempSet = cardSet.copy()
		while len(tempSet) > 0:
			curSet = tempSet.popitem()
			if curSet[0] == "All":
				continue
			currentRarityChecked = curSet[1]
			for j in range(len(currentRarityChecked)):
				currentCard = currentRarityChecked[j]
				if currentCard["cardnumber"] in dupedCards:
					continue
				for k in range(j+1, len(currentRarityChecked)):
					if currentCard["name"] == currentRarityChecked[k]["name"]:
						dupedCards.add(currentCard["cardnumber"])
						dupedCards.add(currentRarityChecked[k]["cardnumber"])
				tempOthers = tempSet.copy()
				while len(tempOthers)>0:
					curOther = tempOthers.popitem()
					if curOther[0] == "All":
						continue
					checkedAgainst = curOther[1]
					for otherCard in checkedAgainst:
						if currentCard["name"] == otherCard["name"]:
							dupedCards.add(currentCard["cardnumber"])
							dupedCards.add(otherCard["cardnumber"])
	return dupedCards

#actually draft
def draft(draftSet, box, playerCount, test, solo, numpacks, custom, cube):
	if not custom and not packInitialised(draftSet):
		return
	data = openSet(draftSet) if not custom else (draftSet.copy() if cube else draftSet)
	#Going to try 6 drafters, 4/pack, but any factor of 24 works
	if numpacks%playerCount != 0:
		print("Invalid player count")
		return
	packsToDraft = []
	if not box:
		for i in range(playerCount):
			packsToDraft.append([])
			for j in range(int(numpacks/playerCount)):
				packsToDraft[i].append(genPack(data, cube, custom, draftSet))
	picks = []
	for pack in packsToDraft:
		picks.append([])
	currentPlayer = 0
	currentPack = 0
	pickNumber = 0
	dupes = detectDuplicate(data, cube)
	while currentPack < numpacks/playerCount:
		#print("Make your next pick by typing a card name (or enough to identify it), or input Review to see past picks, or Inspect and then a card name to see details")
		#Get the pack in a variable so we don't have to keep fetching it
		pack = packsToDraft[(currentPlayer + pickNumber)%playerCount][currentPack]
		#print([card["name"] for card in pack])
		displayedOptions = [(card["name"] if card["cardnumber"] not in dupes else card["cardnumber"] + " " + card["name"]) for card in pack]
		choice = None
		goingForward = True
		if test or (solo and currentPlayer != 0):
			choice = displayedOptions[int(random.random() * len(pack))]
		while choice is None:
			print("Make your next pick by typing a card name (or enough to identify it), or input Review to see past picks, or Inspect and then a card name to see details. Your options:")
			print(", ".join(displayedOptions))
			playerInput = input()
			if playerInput == "Review":
				inspectOptions = [(card["name"] if card["cardnumber"] not in dupes else card["cardnumber"] + " " + card["name"]) for card in picks[currentPlayer]]
				print(", ".join(inspectOptions))
				print("To inspect a card more closely, use Inspect and a card name. To see levels, type Levels, and for the colours of your digimon, Colours. For by-level by-colour, type Spread")
				newInput = input()
				while newInput != "Return":
					if "Inspect" in newInput:
						inspectedCard = interpretInput(inspectOptions, newInput[8:], True)
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
									colourCounts[card["color"]][1] += 1
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
					elif newInput == "Spread":
						print("Values in parenthesis exclude multi-colour cards (which count as both colours otherwise). Only colours with picked cards are shown")
						colourCountsByLevel = {"Red": {}, "Blue": {}, "Yellow": {}, "Green": {}, "Black": {},"Purple": {}, "White": {}}
						for card in picks[currentPlayer]:
							if card["type"] == "Digimon" or card["type"] == "Digi-Egg":
								if card["level"] not in colourCountsByLevel[card["color"]].keys():
									colourCountsByLevel[card["color"]][card["level"]] = [0,0]
								colourCountsByLevel[card["color"]][card["level"]][0] += 1
								if "colour2" in card and card["colour2"] != None:
									if card["level"] not in colourCountsByLevel[card["colour2"]].keys():
										colourCountsByLevel[card["colour2"]][card["level"]] = [0,0]
									colourCountsByLevel[card["colour2"]][card["level"]][0] += 1
								else:
									colourCountsByLevel[card["color"]][card["level"]][1] += 1

						#Loop through the colours, skipping colours with no cards.
						#First set up columns
						topString = "Colour  "
						for i in range(2, 8):
							#8 spaces
							topString += str(i)+("        " if i != 7 else "")
						print(topString)
						for colour, items in colourCountsByLevel.items():
							if len(colour) == 0:
								continue
							outputString = f"{(colour +': '):{8}}"
							for i in range(2, 8):
								if i in items.keys():
									#The most of 1 kind of card you can get is 2 digits, parenthesis also included, so 8 characters wide
									outputString += f"{(str(items[i][0]) +', (' + str(items[i][1]) + ')'):{8}}"
								else:
									outputString += "        "
							print(outputString)
					print("To inspect a card more closely, use Inspect and a card name. To see levels, type Levels, and for the colours of your digimon, Colours. For by-level by-colour, type Spread")
					newInput = input()
			elif "Inspect" in playerInput:
				inspectedCard = interpretInput(displayedOptions, playerInput[8:], False)
				if inspectedCard:
					print(printCard(pack[displayedOptions.index(inspectedCard)]))
			else:
				attemptedPick = interpretInput(displayedOptions, playerInput, False)
				if attemptedPick != None:
					choice = attemptedPick
		#print(choice)
		picks[currentPlayer].append(pack.pop(displayedOptions.index(choice)))
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


#For creating custom sets
def customSet():
	print("Do you want to create a (t)raditional cube where each card appears once, or a (v)irtual set where cards have rarities matching a regular set's distribution?")
	setType = input()
	if setType == "v":
		print("Note, due to adding further complications to the input process without significantly altering gameplay, by default Secret Rare and Alternative Art cards are not included (unless an entire set is imported), and if doing file input will require an additional file")
	elif setType == "t":
		print("A standard digimon draft (4 packs per person) will require 288 cards for 6 people or 384 cards for 8, if you want to emulate cube by having each card appear exactly once then aim for one of these two numbers. If the total number of cards is fewer, cards will be drawn with replacement")
	customSet = [] if setType == "t" else {}
	print("Do you want to add any sets to start with, rather than inputting every card from them? You can add or remove individual cards later. Type a set code (e.g. BT12 or BT8) to add it or Skip to start from scratch")
	if setType == "t":
		print("Note that all cards will be included at the same rate due to being a traditional cube, so be wary of the power difference between the cards added. Also, alternative art versions of cards will not be added as doing so just makes duplicates.")
	hasBase = False
	baseSet = input()
	totalBaseCards = 0
	while baseSet != "Skip":
		hasBase = True
		if packInitialised(baseSet):
			setContents = openSet(baseSet)
			for rarity, cards in setContents.items():
				if rarity != "All":
					if setType == "v":
						customSet.setdefault(rarity, [])
						customSet[rarity] += cards
						totalBaseCards += len(cards)
					else:
						if rarity != "Alternative Art":
							totalBaseCards += len(cards)
							customSet += cards
		else:
			print("Invalid set name. Remember, no dashes in the set name.")
		print("Do you want to add any more sets? Type a set code (e.g. BT12 or BT8) to add it or Skip to continue. Currently " + str(totalBaseCards) + " cards are included.")
		baseSet = input()
	print("Enter f if you wish to import a set from a file, or m if you wish to instead manually enter card codes")
	createType = input()
	if createType == "f":
		print("Please create a decklist in a deckbuilder and export it to a file, then name that file custom.txt and place it in this program's folder."+ (" Include 1 copy of common cards, 2 of uncommon, 3 of rare, and 4 of super rare cards." if setType == "v" else "") + " Press enter when done")
		if setType == "v":
			print("If you want to include secret rare and alternative art rarities in your virtual set, also export a decklist to a file named sec.txt with AA cards at 2 copies and SEC cards at 1 copy. If you don't want them, delete any such file already existing.")
		input()
		countTranslator = ["Common", "Uncommon", "Rare", "Super Rare"]
		secTranslator = ["Secret Rare", "Alternative Art"]
		with open("custom.txt", "r", encoding="utf-8") as f:
			for line in f:
				line = line.rstrip()
				#Capture the card's code to find it
				cardCode = line.split(" ")[-1]
				cardSet = cardCode.split("-")[0]
				print(cardCode)
				if packInitialised(cardSet):
					if setType == "t":
						customSet.append(getCardFromCode(cardCode))
					elif setType == "v":
						cardCategory = countTranslator[int(line.split(" ")[0])-1]
						customSet.setdefault(cardCategory, [])
						customSet[cardCategory].append(getCardFromCode(cardCode))
		if os.path.isfile("sec.txt") and setType == "v":
			with open("sec.txt", "r", encoding="utf-8") as f:
				for line in f:
					line = line.rstrip()
					#Capture the card's code to find it
					cardCode = line.split(" ")[-1]
					cardSet = cardCode.split("-")[0]
					print(cardCode)
					if packInitialised(cardSet):
						cardCategory = secTranslator[int(line.split(" ")[0])-1]
						customSet.setdefault(cardCategory, [])
						customSet[cardCategory].append(getCardFromCode(cardCode))
	elif createType == "m":
		#Going to stop trying cute ternery stuff
		if setType == "t":
			print("Type in a card's code (for example: BT11-046) to add it to the cube. Type End when done.")
			cardToAdd = input()
			while cardToAdd != "End":
				customSet.append(getCardFromCode(cardToAdd))
				print("Type in a card's code (for example: BT11-046) to add it to the cube. Type End when done.")
				cardToAdd = input()
		elif setType == "v":
			cardRarities = ["Common", "Uncommon", "Rare", "Super Rare", "Secret Rare", "Alternative Art"]
			for rarity in cardRarities:
				if not hasBase and (rarity == "Secret Rare" or rarity == "Alternative Art"):
					print("Do you want to add any cards into the " + rarity + " rarity? Type y if so, or n to skip this rarity")
					skipChoice = input()
					if skipChoice == "n":
						continue
				customSet.setdefault(rarity, [])
				print("Type in a card's code (for example: BT10-046) to add it to list of "+ rarity +"s. Type End to go to the next category.")
				cardToAdd = input()
				while cardToAdd != "End":
					customSet[rarity].append(getCardFromCode(cardToAdd))
					print("Type in a card's code (for example: BT10-046) to add it to list of "+ rarity +"s. Type End to go to the next category.")
					cardToAdd = input()
			
	if hasBase:
		print("Do you want to remove any cards? Type y if yes, s to skip, or Swap if you wish to swap to the other input method at this stage.")
		if(createType == "f"):
			print("This is most useful for importing a large amount of cards from file to add to an existing set and then removing 1-2 individual cards afterwards")
		removeType = input()
		if removeType == "Swap":
			removeType = "f" if createType == "m" else "m"
		elif removeType == "y":
			removeType = createType
		if removeType != "s":
			if removeType == "m":
				print("Type a card code to remove it, or End to skip" + (", or either Alternative Art or Secret Rare to remove that entire category of cards. You can also append to a card code a rarity to remove that card from specifically that rarity (e.g. BT11-103 Uncommon)" if setType == "v" else "."))
				cardToRemove = input()
				while cardToRemove != "End":
					if setType == "v" and (cardToRemove == "Alternative Art" or cardToRemove == "Secret Rare"):
						if cardToRemove in customSet.keys():
							del customSet[cardToRemove]
						else:
							print("That rarity already did not exist.")
					else:
						cardObjectToRemove = getCardFromCode(cardToRemove.split()[0])
						if setType == "v":
							if len(cardToRemove.split()) == 2:
								cardToRemove, targetRarity = cardToRemove.split()
								if targetRarity not in customSet.keys():
									print("That rarity does not exist in this set")
								else:
									if cardObjectToRemove["name"] in [card["name"] for card in customSet[targetRarity]]:
										customSet[targetRarity].pop(findCardIndex(cardObjectToRemove["name"], customSet[targetRarity]))
									else:
										print("That card is not found in that rarity")
							else:
								foundCard = False
								for rarity, cards in customSet.items():
									#Unfortunately since people can set custom rarity of cards, the rarity of the card in the database doesn't work
									#It's probably faster to compare strings and make a list of strings than to compare the whole object
									if cardObjectToRemove["name"] in [card["name"] for card in cards]:
										customSet[rarity].pop(findCardIndex(cardObjectToRemove["name"], customSet[rarity]))
										foundCard = True
								if not foundCard:
									print("That card already wasn't in the set.")
						else:
							if cardObjectToRemove["name"] in [card["name"] for card in customSet]:
								customSet.pop(findCardIndex(cardObjectToRemove["name"], customSet))
					print("Do you want to remove any other cards from the card pool? Type a card code to remove it, or End to stop removing" +("." if setType == "t" else ", or Alternative Art or Secret Rare to remove that entire category."))
					cardToRemove = input()
			elif removeType == "f":
				print("Since you imported 1 or more sets to start with, do you want to remove any cards those sets came with? If so, export a new decklist of the cards to remove and save it as remove.txt. " + (" Include 1 copy of common cards, 2 of uncommon, 3 of rare, and 4 of super rare cards." if setType == "v" else "") + " Press enter when done")
				if setType == "v":
					print("If you want to remove cards from the secret rare and alternative art rarities, also export a decklist to a file named removeSec.txt with AA cards at 2 copies and SEC cards at 1 copy. Additionally, any line included in the file reading as Alternative Art or Secret Rare will instead remove that entire category (and any cards added to it before that line).")
				input()
				if os.path.isfile("remove.txt"):
					#To speed things up, collect all the values to remove
					cardsToRemove = [] if setType == "t" else {}
					with open("remove.txt", "r", encoding="utf-8") as f:
						for line in f:
							line = line.rstrip()
							#Capture the card's code to find it
							cardCode = line.split(" ")[-1]
							cardSet = cardCode.split("-")[0]
							print(cardCode)
							if packInitialised(cardSet):
								if setType == "t":
									cardsToRemove.append(cardCode)
								elif setType == "v":
									cardCategory = countTranslator[int(line.split(" ")[0])-1]
									cardsToRemove.setdefault(cardCategory, [])
									cardsToRemove[cardCategory].append(cardCode)
					#Now for high rarities
					if os.path.isfile("removeSec.txt") and setType == "v":
						with open("removeSec.txt", "r", encoding="utf-8") as f:
							for line in f:
								line = line.rstrip()
								#For removing whole categories
								if setType == "v" and (line == "Secret Rare" or line == "Alternative Art"):
									if line in customSet.keys():
										del customSet[line]
								else:
									cardCategory = secTranslator[int(line.split(" ")[0])-1]
									cardsToRemove.setdefault(cardCategory, [])
									cardsToRemove[cardCategory].append(cardCode)
					#And now to actually remove
					if setType == "t":
						customSet[:] = [card for card in customSet if card not in cardsToRemove]
					else:
						for rarity, cards in cardsToRemove.items():
							if rarity in customSet.keys():
								customSet[rarity][:] = [card for card in customSet[rarity] if card not in cardsToRemove]
	while True:
		print("Press r to view the list of cards, e to export the set to a file, or d to draft them, any other key to exit")
		playerChoice = input()
		if playerChoice == "r":
			if setType == "t":
				for card in customSet:
					print(card["name"] + " " + card["cardnumber"])
			else:
				for rarity, contents in customSet.items():
					print(rarity)
					for card in contents:
						print(card["name"] + " " + card["cardnumber"])
					print("\n")
		elif playerChoice == "d":
			potentialCopy = None if setType == "v" else customSet.copy()
			draft(customSet, False, 8, False, True, 24, True, setType == "t")
			if potentialCopy != None:
				customSet = potentialCopy
		elif playerChoice == "e":
			print("After you press enter, this custom set will be written to the file completeCustom.txt, so make sure to copy it elsewhere if you want to keep its current contents")
			input()
			with open("completeCustom.txt", "w", encoding="utf-8") as f:
				f.write(setType + "\n")
				if setType == "v":
					for rarity, cards in customSet.items():
						f.write(rarity + "\n")
						for card in cards:
							f.write(card["cardnumber"] + "\n")
						f.write("\n")
				else:
					for card in customSet:
						f.write(card["cardnumber"] + "\n")
		else:
			break


#Function for unpacking an exported set
def unpackSet():
	print("Name the file to import customImport.txt and put it in this program's folder, then press enter to continue")
	input()
	if os.path.isfile("customImport.txt"):
		customSet = None
		setType =  None
		with open("customImport.txt", "r", encoding="utf-8") as f:
			setType = f.readline().rstrip()
			currentRarity = None
			print(setType)
			customSet = [] if setType == "t" else {}
			for line in f:
				line = line.rstrip()
				print(line)
				if setType == "v" and currentRarity == None:
					currentRarity = line
					customSet[currentRarity] = []
				elif line == "":
					currentRarity = None
				else:
					if setType == "v":
						customSet[currentRarity].append(getCardFromCode(line))
					else:
						customSet.append(getCardFromCode(line))
		print("Do you want to view the cards? Type e if so")
		if input() == "e":
			if setType == "t":
				for card in customSet:
					print(card["name"] + " " + card["cardnumber"])
			else:
				for rarity, cards in customSet.items():
					print(rarity)
					for card in cards:
						print(card["name"] + " " + card["cardnumber"])
					print("")
		print("Do you want to draft the imported set? y if so.")
		if input() == "y":
			draft(customSet, False, 8, False, True, 24, True, setType == "t")
#moveAA("EX4")

def menu():
	print("What would you like to do? Type d to draft, c to make a custom set, or i to import a custom set to view or draft. Type Close to close")
	menuChoice = input()
	while menuChoice != "Close":
		if menuChoice == "d":
			draft("BT12", False, 4, False, True, 24, False, False)
		elif menuChoice == "c":
			customSet()
		elif menuChoice == "i":
			unpackSet()
		print("What would you like to do? Type d to draft, c to make a custom set, or i to import a custom set to view or draft. Type Close to close")
		menuChoice = input()

menu()