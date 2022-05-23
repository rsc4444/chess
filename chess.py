import pandas as pd
import random
import sys

# ====================================================================================================
# KONSTANTEN + Variablen
# ====================================================================================================

board = [
["br","bn","bb","bq","bk","bb","bn","br"],
["bp","bp","bp","bp","bp","bp","bp","bp"],
["--","--","--","--","--","--","--","--"],
["--","--","--","--","--","--","--","--"],
["--","--","--","--","--","--","--","--"],
["--","--","--","--","--","--","--","--"],
["wp","wp","wp","wp","wp","wp","wp","wp"],
["wr","wn","wb","wq","wk","wb","wn","wr"],
]

LETTERS 		= ("a","b","c","d","e","f","g","h")
NUMBERS 		= ("8","7","6","5","4","3","2","1")
DIRECTIONS_RBQK = [(-1,0),(+1,0),(0,+1),(0,-1),(-1,+1),(+1,-1),(+1,+1),(-1,-1)]
DIRECTIONS_N 	= [(-2,+1),(-1,+2),(+1,+2),(+2,+1),(+2,-1),(+1,-2),(-1,-2),(-2,-1)]
OTHERCOLOR 		= {"w":"b","b":"w"}
board 			= pd.DataFrame(board,index=NUMBERS,columns=LETTERS)
boardCopy 		= []
# FEN

# ====================================================================================================
# Prüfe bestimmte Zustände
# ====================================================================================================

def checkDrawCheckmate(color,moveHistory,boardCopy,kingInCheck,capturableEnPassant):
	totalValuePieces 	= 0
	lightSquaredBishops = 0
	darkSquaredBishops 	= 0
	legalMovesV1 		= []
	legalMovesV2 		= []

	boardCopy.append(board.values.tolist())
	if boardCopy.count(board.values.tolist()) == 3:
		sys.exit("Threefold repetition! This is a draw.")

	# (Figuren)werte zählen für Remisprüfung durch zu wenig Material + legale Züge speichern für Patt- und Mattprüfung
	for sourceRank in range(8):
		for sourceLine in range(8):
			piece = board.iloc[sourceRank,sourceLine]
			if piece == "--": continue
			elif piece.endswith("p") or piece.endswith("q") or piece.endswith("r"): # Bauer / Dame / Turm
				totalValuePieces += 9
			elif piece.endswith("n"): # Springer
				totalValuePieces += 3
			elif piece.endswith("b"): # Läufer
				totalValuePieces += 3
				if (sourceRank + sourceLine) % 2 == 0: # Indizes beide gerade oder beide ungerade => weißes Feld
					lightSquaredBishops += 1
				else: # Indizes 1x gerade und 1x ungerade => schwarzes Feld
					darkSquaredBishops += 1 

			# Wenn piece = eigene Figur
			if piece.startswith(color):
				legalMovesV1.clear()
				legalMovesV1 = checkLegalMovesV1(piece,legalMovesV1,sourceRank,sourceLine,capturableEnPassant)
				legalMovesV2 = checkLegalMovesV2(color,piece,legalMovesV1,legalMovesV2,sourceRank,sourceLine)

	# Nur Leichtfigur ODER nur weißfeldrige Läufer ODER nur schwarzfeldrige Läufer auf dem Brett (neben den Königen) => Unentschieden.
	# if totalValuePieces <= 3 or lightSquaredBishops*3 == totalValuePieces or darkSquaredBishops*3 == totalValuePieces:
	if totalValuePieces <= 3 or (lightSquaredBishops or darkSquaredBishops)*3 == totalValuePieces:
		sys.exit("\nNot enough mating material! This is a draw.\n")

	# Wenn keine legalen Züge... und König nicht im Schach => Patt ...und König im Schach => Matt
	if not legalMovesV2 and not kingInCheck:
		sys.exit("\nStalemate! This is a draw.\n")
	elif not legalMovesV2 and kingInCheck:
		sys.exit(f"\nCheckmate! {'White' if color == 'w' else 'Black'} wins.\n")

	# Mindestens 50 Züge in Folge kein Bauern- oder Schlagzug oder Umwandlung => Unentschieden.
	if (len_moveHistory := len(moveHistory)) >= (2*50):
		for i in range(len_moveHistory,len_moveHistory-(2*50),-1):
			if (moveHistory[i-1][0][1] == "p") or moveHistory[i-1][3] or moveHistory[i-1][4]: break
		else:
			sys.exit("\n50 moves without moving a pawn, taking a piece or mating the king! This is a draw.\n")


def isKingInCheck(color) -> bool:
	# Iteration über das Brett. Wenn eigener König gefunden => prüfe, ob dieser im Schach steht (return True/False)
	for sourceRank in range(8):
		for sourceLine in range(8):
			if board.iloc[sourceRank,sourceLine] == color+"k":
				return isUnderAttack(color,sourceRank,sourceLine)


def checkShortCastlingRight(piece,moveHistory,backRank) -> bool:
	# Wenn König und Turm auf Ausgangsfeld stehen und Felder dazwischen frei => weitermachen
	if board.loc[backRank,"e"]==piece[0]+"k" and board.loc[backRank,"f"]=="--" and board.loc[backRank,"g"]=="--" and board.loc[backRank,"h"]==piece[0]+"r":
		# Wenn König oder Turm schon bewegt wurden => Rochade nicht möglich, sonst (vorerst) möglich
		for move in moveHistory:
			if move[1]=="e"+backRank or move[1]=="h"+backRank or move[2]=="h"+backRank:
				return False
		return True
	return False


def checkLongCastlingRight(piece,moveHistory,backRank) -> bool:
	if board.loc[backRank,"a"]==piece[0]+"r" and board.loc[backRank,"b"]=="--" and board.loc[backRank,"c"]=="--" and board.loc[backRank,"d"]=="--" and board.loc[backRank,"e"]==piece[0]+"k":
		for move in moveHistory:
			if move[1]=="a"+backRank or move[2]=="a"+backRank or move[1]=="e"+backRank:
				return False
		return True
	return False


def checkCastleMovesV1(piece,kingInCheck,legalMovesV1,moveHistory) -> tuple:
	backRank = "1" if piece.startswith("w") else "8"
	shortCastlingRight 	= checkShortCastlingRight(piece,moveHistory,backRank)
	longCastlingRight 	= checkLongCastlingRight(piece,moveHistory,backRank)

	backRank = 7 if piece.startswith("w") else 0
	# König muss am Zug sein und darf nicht im Schach stehen => füge Rochadezüge hinzu
	if piece.endswith("k") and not kingInCheck and shortCastlingRight:
		legalMovesV1.extend([[backRank,6],[backRank,7]])
	if piece.endswith("k") and not kingInCheck and longCastlingRight:
		legalMovesV1.extend([[backRank,0],[backRank,2]])

	return legalMovesV1, shortCastlingRight, longCastlingRight

# ====================================================================================================
# Filtere legale Zugmöglichkeiten
# ====================================================================================================

def checkLegalMovesV1(piece,legalMovesV1,sourceRank,sourceLine,capturableEnPassant) -> list:
	if piece[1] == "p":
		return checkLegalMovesPawns(piece,legalMovesV1,sourceRank,sourceLine,capturableEnPassant)
	else:
		return checkLegalMovesPieces(piece,legalMovesV1,sourceRank,sourceLine)


def checkLegalMovesV2(color,piece,legalMovesV1,legalMovesV2,sourceRank,sourceLine) -> list:
	backRank = 7 if color == "w" else 0 # (Grund)reihe in Abhängigkeit von Farbe (schwarz/weiß)

	# "checkCastleMovesV2" || Prüfung, ob Rochadezug vorliegt und ob diese durchgeführt werden kann (König darf nicht ins Schach)
	for move in legalMovesV1.copy():
		summand07 = 0 if move in [[backRank,6],[backRank,7]] else 7 # (Grund)reihe in Abhängigkeit von Rochade (kurz/lang)
		summand08 = 0 if move in [[backRank,6],[backRank,7]] else 8 # Linie in Abhängigkeit von Rochade (kurz/lang)
		# Beide Rochadezüge (Zielfeld = Königsfeld/Turmfeld) prüfen | Zwischenschritt + Zielfeld dürfen nicht bedroht sein
		if piece.endswith("k") and board.iloc[backRank,abs(4-summand08)] == color+"k" and move in [[backRank,abs(6-summand08)],[backRank,abs(7-summand07)]]:
			# 1. Königsschritt gehen (Zwischenschritt)
			board.iloc[backRank,abs(4-summand08)] = "--"
			board.iloc[backRank,abs(5-summand08)] = color+"k"			
			if isKingInCheck(color): # Wenn König im Schach => Rochadezug entfernen + Ausgangsstellung wiederherstellen + nächster Zug
				legalMovesV1.remove(move)
				board.iloc[backRank,abs(5-summand08)] = "--"
				board.iloc[backRank,abs(4-summand08)] = color+"k"
				continue			
			else: # Wenn König nach 1. Königsschritt nicht im Schach => 2. Königsschritt gehen (Zielfeld)
				board.iloc[backRank,abs(5-summand08)] = "--"
				board.iloc[backRank,abs(6-summand08)] = color+"k"				
				if isKingInCheck(color): # Wenn König im Schach => Rochadezug entfernen + Ausgangsstellung wiederherstellen + nächster Zug
					legalMovesV1.remove(move)
					board.iloc[backRank,abs(6-summand08)] = "--"
					board.iloc[backRank,abs(4-summand08)] = color+"k"
					continue				
				else: # Wenn König auch nach 2. Königsschritt nicht im Schach =>  Ausgangsstellung wiederherstellen
					board.iloc[backRank,abs(6-summand08)] = "--"
					board.iloc[backRank,abs(4-summand08)] = color+"k"
					# Turm darf als Zielfeld gewählt werden, auch wenn es bedroht ist | ohne continue wäre remove im Anschluss, da Turmfeld im Schach
					if move == [backRank,abs(7-summand07)]: continue
		
		enterSquare = board.iloc[move[0],move[1]] 	# Inhalt von Zielfeld zwischenspeichern, um move später zu resetten	
		board.iloc[sourceRank,sourceLine] = "--" 	# Zug ausführen (Quellfeld = "--" ...
		board.iloc[move[0],move[1]] = piece 		# ... und Zielfeld = die gewählte Figur)

		# Wenn mein König nach dem getesteten legalMove im Schach steht, wird dieser Zug entfernt
		if isKingInCheck(color):
			legalMovesV1.remove(move)
		
		board.iloc[move[0],move[1]] = enterSquare # Nach Prüfung Zug zurück (Zielfeld = Figur, die vorher da stand ...
		board.iloc[sourceRank,sourceLine] = piece # ... und Quellfeld = die gewählte Figur)

	for lmv1 in legalMovesV1:
		legalMovesV2.append(lmv1)
	return legalMovesV2


def checkLegalMovesPawns(piece,legalMovesV1,sourceRank,sourceLine,capturableEnPassant) -> list:
	summand = 7 if piece.startswith("b") else 0 # Für Position: ggü-liegende Reihen/Linien von Schwarz und Weiß ergeben 7
	factor = -1 if piece.startswith("b") else 1 # Für Zug: (Schlag)Richtung der Bauern von schwarz und weiß haben umgekehrte Vorzeichen
	# Wenn Bauer in 2./7. Reihe und beide Felder davor frei => füge Zug hinzu
	if sourceRank == abs(6-summand) and board.iloc[sourceRank-1*factor,sourceLine] == "--" and board.iloc[sourceRank-2*factor,sourceLine] == "--":
		legalMovesV1.append([sourceRank-2*factor,sourceLine])
	# Wenn Bauer in 5./4. Reihe und links/rechts ein gegn. Bauer steht, der gerade einen Doppelschritt gegangen ist => füge Zug hinzu
	elif sourceRank == abs(3-summand) and sourceLine != abs(0-summand) and capturableEnPassant == [sourceRank,sourceLine-1*factor]:
		legalMovesV1.append([sourceRank-1*factor,sourceLine-1*factor])
	elif sourceRank == abs(3-summand) and sourceLine != abs(7-summand) and capturableEnPassant == [sourceRank,sourceLine+1*factor]:
		legalMovesV1.append([sourceRank-1*factor,sourceLine+1*factor])
	# Immer und unabhängig von Reihe: Feld davor frei? Schlagzug nach links/rechts möglich? => füge Zug hinzu
	if board.iloc[sourceRank-1*factor,sourceLine] == "--":
		legalMovesV1.append([sourceRank-1*factor,sourceLine])
	if sourceLine != abs(0-summand) and board.iloc[sourceRank-1*factor,sourceLine-1*factor].startswith(OTHERCOLOR[piece[0]]):
		legalMovesV1.append([sourceRank-1*factor,sourceLine-1*factor])
	if sourceLine != abs(7-summand) and board.iloc[sourceRank-1*factor,sourceLine+1*factor].startswith(OTHERCOLOR[piece[0]]):
		legalMovesV1.append([sourceRank-1*factor,sourceLine+1*factor])
	return legalMovesV1


def checkLegalMovesPieces(piece,legalMovesV1,sourceRank,sourceLine) -> list:
	directions = DIRECTIONS_N if piece[1] == "n" else DIRECTIONS_RBQK # Springer hat andere Richtungen als der Rest der Figuren
	for direction in directions:
		for step in range(1,8):
			# Bei Läufer müssen die geraden und bei Turm die diagonalen Züge ausgeschlossen werden
			if ((piece[1] != ("b") and direction in directions[:4]) or (piece[1] != ("r") and direction in directions[4:])):
				stepRank, stepLine = step*direction[0], step*direction[1]
				if not ((0 <= sourceRank+stepRank <= 7) and (0 <= sourceLine+stepLine <= 7)): break   # Index außerhalb => nächste Richtung
				if board.iloc[sourceRank+stepRank,sourceLine+stepLine].startswith(piece[0]): break 	  # Eigene Figur im Weg => nächste Richtung
				if board.iloc[sourceRank+stepRank,sourceLine+stepLine].startswith(OTHERCOLOR[piece[0]]): # Gegner im Weg => Zug hinzu + nächste Richtung
					legalMovesV1.append([sourceRank+stepRank,sourceLine+stepLine])
					break
				if board.iloc[sourceRank+stepRank,sourceLine+stepLine] == "--": # Feld frei => Zug hinzu + nächster Schritt
					legalMovesV1.append([sourceRank+stepRank,sourceLine+stepLine])
				if piece[1] in ("k","n"): break # König/Springer kann nur einen Schritt gehen, daher Abbruch vor 2. step
			else: break # Richtung passt nicht zur Figur => nächste Richtung
	return legalMovesV1

# ====================================================================================================
# Führe bestimmte Zugaktionen durch
# ====================================================================================================
	
def promote(piece,targetRank,playerWhite,playerBlack) -> tuple:
	# Checke, ob Umwandlung stattgefunden hat und speichere die Information + die Figur
	promotion = False
	if piece.endswith("p") and targetRank in [0,7]:
		if (playerWhite == "human" and piece.startswith("w")) or (playerBlack == "human" and piece.startswith("b")):
			piece = piece[0] + input("\nPromote to:\nq (Queen)\nr (Rook)\nb (Bishop)\nn (Knight)\n")
		elif (playerWhite == "engine" and piece.startswith("w")) or (playerBlack == "engine" and piece.startswith("b")):
			print("\nPromote to:\nq (Queen)\nr (Rook)\nb (Bishop)\nn (Knight)\n")
			piece = piece[0] + random.choice(["q","r","b","n"])
			print(piece[1]+"\n")
		promotion = True
	return piece, promotion


def move(piece,shortCastlingRight,longCastlingRight,sourceRank,sourceLine,targetRank,targetLine,capturableEnPassant) -> bool:
	hasTakenPiece = False
	backRank = 7 if piece.startswith("w") else 0
	
	# kurze / lange Rochade
	if piece.endswith("k") and shortCastlingRight and targetLine in [6,7]:
		board.iloc[backRank,4] = "--"
		board.iloc[backRank,6] = piece[0]+"k"
		board.iloc[backRank,7] = "--"
		board.iloc[backRank,5] = piece[0]+"r"

	elif piece.endswith("k") and longCastlingRight and targetLine in [0,2]:
		board.iloc[backRank,4] = "--"
		board.iloc[backRank,2] = piece[0]+"k"
		board.iloc[backRank,0] = "--"
		board.iloc[backRank,3] = piece[0]+"r"
	
	else: # Jeder Nich-Rochade-Zug. Altes Feld räumen, neues Feld mit gezogener Figur besetzen
		board.iloc[sourceRank,sourceLine] = "--"
		board.iloc[targetRank,targetLine] = piece
	
	if board.iloc[targetRank,targetLine][0] == OTHERCOLOR[piece[0]]: hasTakenPiece = True # Wenn auf Zielfeld Gegner steht => Schlagzug

	enpassantRank = 3 if piece.startswith("w") else 4
	# Wenn enPassant möglich war UND ich weißen Bauer hatte UND ich auf 5. Reihe stand UND Spalte Zielfeld war Spalte gegenerischer Bauer
	if len(capturableEnPassant) == 2 and  piece == piece[0]+"p" and sourceRank == enpassantRank and targetLine == capturableEnPassant[1]:
		# Dann gegenerischen Bauer eliminieren => Schlagzug
		board.iloc[capturableEnPassant[0],capturableEnPassant[1]] = "--"
		hasTakenPiece = True

	return hasTakenPiece


def checkIfWeDoubleSteppedPawn(piece,sourceRank,targetRank,targetLine) -> list:
	# Checke, ob wir gerade einen Bauern mit Doppelschritt bewegt haben, der als Nächstes durch enPassant vom Gegner geschlagen werden kann
	capturableEnPassant = []
	if piece.endswith("p") and abs(targetRank-sourceRank) == 2:
		capturableEnPassant = [targetRank,targetLine]
	return capturableEnPassant


def attackedByOpponent(dangerFields,piece) -> bool:
	for df in dangerFields:
		if board.iloc[df[0],df[1]] == OTHERCOLOR[piece[0]] + piece[1]:	return True
	return False


def isUnderAttack(color,myRank,myLine) -> bool:
	piece 			= color+"p" # Bauer
	dangerFields 	= []
	factor 			= -1 if color == "b" else 1

	# wenn Feld links oben bzw. rechts oben innerhalb Brett => Feld speichern und später prüfen, ob da gegn. Bauer steht
	if ((0 <= myRank-1*factor <= 7) and (0 <= myLine-1*factor <= 7)):
		dangerFields.append([myRank-1*factor,myLine-1*factor])
	if ((0 <= myRank-1*factor <= 7) and (0 <= myLine+1*factor <= 7)):
		dangerFields.append([myRank-1*factor,myLine+1*factor])
	if attackedByOpponent(dangerFields,piece): return True

	# Vom Standpunkt des Königs werden Bauern/Springer/Läufer/Turm/Damen/Königszüge gegangen (dangerFields)
	# Wenn in solch einem Feld die jeweilige gegnerische Figur steht => König angegriffen => return True; sonst return False
	for shortcut in ["r","b","q","n","k"]:  # Turm / Läufer / Dame / Springer / König
		piece = color+shortcut
		dangerFields.clear()
		dangerFields = checkLegalMovesPieces(piece,dangerFields,myRank,myLine)
		if attackedByOpponent(dangerFields,piece): return True
		
	return False

# ====================================================================================================
# Starte Spiel, Schwarz und Weiß sind abwechselnd dran
# ====================================================================================================

def selectPlayerType(playerColor) -> str:
	while True:
		playerType = input(f"\nplayer {playerColor}:\n h (human) \n e (engine)\n\n")
		if playerType == "h": return "human"
		elif playerType == "e": return "engine"


def getPlayerCoords(playerWhite, playerBlack, color, inputMessage):
	while True:
		if (playerWhite == "human" and color == "w") or (playerBlack == "human" and color == "b"):
			inp = input(f"{inputMessage}: ")
		elif (playerWhite == "engine" and color == "w") or (playerBlack == "engine" and color == "b"):
			inp = random.choice(LETTERS)+random.choice(NUMBERS)
			
		# Eingabe muss aus zwei Zeichen bestehen: 1. Zeichen a-h und 2. Zeichen 1-8
		if len(inp) == 2 and inp[0] in LETTERS and inp[1] in NUMBERS:
			piece = board.loc[inp[1],inp[0]]  					# Figur auf "From"-Feld, z.B. "wp" oder "bp"
			rank  = int(NUMBERS.index(inp[1]))  				# Zahl/Reihe in Indexform [0-7]
			line  = int(LETTERS.index(inp[0]))  				# Buchstabe/Linie in Indexform [0-7]
			if inputMessage == "From" and piece[0] == color: 	# Wenn Farbe am Zug gleich der Farbe der zu bewegenden Figur
				return (piece, rank, line, inp)
			elif inputMessage == "To":
				return (rank, line, inp)


def startGame():
	moveHistory 		= []  # Zughstorie
	capturableEnPassant = []  # Bauern, die der Ziehende enPassant schlagen kann
	color 				= "w" # Weiß beginnt
	legalMovesV1		= []
	legalMovesV2		= []

	print("\nWelcome to my chess game!")
	# playerWhite, playerBlack = selectPlayerType("White"), selectPlayerType("Black")
	playerWhite, playerBlack = "human", "human"
	print(board)

	while True:
		kingInCheck = isKingInCheck(color) # Mein König im Schach?
		checkDrawCheckmate(color,moveHistory,boardCopy,kingInCheck,capturableEnPassant) # Remis-/Mattstellung?

		print(f"\n{'White' if color == 'w' else 'Black'} to move:")
		while True:
			piece, sourceRank, sourceLine, sourceSquare = getPlayerCoords(playerWhite, playerBlack, color, "From")

			# Prüfe Züge ohne Beachtung von Schach / ggf. füge Rochadezüge hinzu ohne Beachtung von Schach / ggf. entferne Züge, nach denen der König im Schach
			legalMovesV1.clear()
			legalMovesV1 		= checkLegalMovesV1(piece,legalMovesV1,sourceRank,sourceLine,capturableEnPassant)
			legalMovesV1,\
			shortCastlingRight,\
			longCastlingRight 	= checkCastleMovesV1(piece,kingInCheck,legalMovesV1,moveHistory)
			legalMovesV2.clear()
			legalMovesV2 		= checkLegalMovesV2(color,piece,legalMovesV1,legalMovesV2,sourceRank,sourceLine)

			# Weiter gehts nur, wenn legaler Zug mit der Figur möglich, sonst Wdh. Eingabe (break)
			if legalMovesV2:
				# Bei Engine wird gewähltes Feld jetzt ausgegeben, also erst nachdem legales Feld gefunden wurde
				if (playerWhite == "engine" and color == "w") or (playerBlack == "engine" and color == "b"):
					print("From:",sourceSquare)
				break

		while True:
			targetRank, targetLine, targetSquare = getPlayerCoords(playerWhite, playerBlack, color, "To")
			
			if [targetRank,targetLine] not in legalMovesV2: continue # Wiederholung Eingabe, wenn Zielfeld nicht legal

			# Bei Engine wird gewähltes Feld jetzt ausgegeben, also erst nachdem legales Feld gefunden wurde
			if (playerWhite == "engine" and color == "w") or (playerBlack == "engine" and color == "b"):
				print("To:",targetSquare)

			# ggf. umwandeln / ggf. enPassant geschlagenen Bauern eliminieren / immer Figur ziehen / ggf. gegangenen Doppelschritt merken / Zughistorie
			piece, promotion 	= promote(piece,targetRank,playerWhite,playerBlack)
			hasTakenPiece 		= move(piece,shortCastlingRight,longCastlingRight,sourceRank,sourceLine,targetRank,targetLine,capturableEnPassant)
			capturableEnPassant = checkIfWeDoubleSteppedPawn(piece,sourceRank,targetRank,targetLine)
			moveHistory.append([piece,sourceSquare,targetSquare,hasTakenPiece,promotion])
			break

		print()
		print(board)
		color = "w" if color == "b" else "b" # Farbe wechseln

if __name__=="__main__":
	startGame()