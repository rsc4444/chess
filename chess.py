import copy
import numpy as np
import pandas as pd
import random
import sys
import time

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

NUMBERS 		= ("8","7","6","5","4","3","2","1")
LETTERS 		= ("a","b","c","d","e","f","g","h")
otherColor		= {"w": "b", "b": "w"}

board = pd.DataFrame(board,index=NUMBERS,columns=LETTERS)

boardComposition = board.values.tolist()
boardCompositions = []
boardCompositions.append(boardComposition)

# ====================================================================================================
# FLIP board
# ====================================================================================================

# def flipBoard(color,board):
# 	for y in range(4):
# 		for x in range(8):
# 			board[y][x], board[7-y][7-x] = board[7-y][7-x], board[y][x]
# 	i = -1 if color[0].lower() == "b" else 1
# 	return pd.DataFrame(board, index = NUMBERS[::i], columns = LETTERS[::i])

# ====================================================================================================
# Prüfe bestimmte Zustände
# ====================================================================================================

def checkDrawCheckmate(color,moveHistory,boardCompositions,isMyKingInCheck,capturableEnPassant):

	totalValuePieces 	= 0
	lightSquaredBishops = 0
	darkSquaredBishops 	= 0
	legalMovesV3 		= []
	fiftyMovesDraw 		= False

	boardComposition = board.values.tolist()
	boardCompositions.append(boardComposition)

	# Nach Schlag- oder Bauernzug Liste leeren, um Rechenleistung zu sparen => wirkungslos?
	# if moveHistory and (moveHistory[-1][0][1] == "p" or moveHistory[-1][3] or moveHistory[-1][4]):
	# 	boardCompositions = []

	if boardCompositions.count(boardComposition) == 3:
		sys.exit("Threefold repetition! This is a draw.")

	# Alle 64 Felder durchgehen und (Figuren)werte zählen für Remisprüfung durch zu wenig Material
	# Alle 64 Felder durchgehen und legale Züge speichern für Patt- und Mattprüfung
	for sourceSquareRank in range(8):
		for sourceSquareLine in range(8):
			piece = board.iloc[sourceSquareRank,sourceSquareLine]
			# p = pawn (Bauer), q = queen (Dame), r = rook (Turm), n = knight (Springer), b = bishop (Läufer)
			if piece[1] == "p" or piece[1] == "q" or piece[1] == "r":
				totalValuePieces += 9
			elif piece[1] == "n":
				totalValuePieces += 3
			elif piece[1] == "b":
				totalValuePieces += 3
				# Zeilen- und Spaltenindex 2x gerade oder 2x ungerade => weißes Feld (es geht hier nur um die Feldfarbe, nicht um die Figurenfarbe!!!)
				if (sourceSquareRank % 2) == (sourceSquareLine % 2):
					lightSquaredBishops += 1
				# Zeilen- und Spaltenindex 1x gerade und 1x ungerade => schwarzes Feld (es geht hier nur um die Feldfarbe, nicht um die Figurenfarbe!!!)
				elif (sourceSquareRank % 2) != (sourceSquareLine % 2):
					darkSquaredBishops += 1

			# Wenn piece = eigene Figur
			if (piece[0] == color[0].lower()):
				legalMovesV1 = []
				legalMovesV1 = checkLegalMovesV1(color,piece,legalMovesV1,sourceSquareRank,sourceSquareLine,capturableEnPassant)
				legalMovesV2 = checkLegalMovesV2(color,piece,legalMovesV1,legalMovesV3,sourceSquareRank,sourceSquareLine)

	# Mindestens 50 Züge in Folge kein Bauern- oder Schlagzug => Unentschieden.
	if len(moveHistory) >= (2*50):
		fiftyMovesDraw = True
		# Gehe letzte 50 Züge durch
		for i in range(len(moveHistory),len(moveHistory)-(2*50),-1):
			# Wenn Bauernzug oder Schlagzug oder Umwandlung => kein Unentschieden.
			if (moveHistory[i-1][0][1] == "p") or moveHistory[i-1][3] or moveHistory[i-1][4]:
				fiftyMovesDraw = False
				break

	# Nur Leichtfigur ODER nur weißfeldrige Läufer ODER nur schwarzfeldrige Läufer auf dem Brett (neben den Königen) => Unentschieden.
	if (totalValuePieces <= 3) or (lightSquaredBishops * 3 == totalValuePieces) or (darkSquaredBishops * 3 == totalValuePieces):
		sys.exit("\nNot enough mating material! This is a draw.\n")

	# Wenn keine legalen Züge...
	if not legalMovesV2:
		# ...aber König nicht im Schach => Patt
		if not isMyKingInCheck:
			sys.exit("\nStalemate! This is a draw.\n")
		# ...und König im Schach => Matt
		if isMyKingInCheck:
			color = "White" if color == "Black" else "Black"
			sys.exit("\nCheckmate! "+color+" wins.\n")

	if fiftyMovesDraw:
		sys.exit("\n50 moves without moving a pawn, taking a piece or mating the king! This is a draw.\n")


def checkIfKingInCheck(color) -> bool:
	# Iteration über das Brett. Feld mit eigenem König wird gesucht
	for sourceSquareRank in range(8):
		for sourceSquareLine in range(8):
			# Wenn eigener König gefunden
			if board.iloc[sourceSquareRank,sourceSquareLine] == color[0].lower()+"k":
				# prüfe, ob Feld mit eigenem König im Schach (return True = im Schach / return False = nicht im Schach)
				return isUnderAttack(color,sourceSquareRank,sourceSquareLine)


def checkShortCastleRight(color,moveHistory) -> bool:
	# Prüfe Recht für kurze Rochade weiß
	# Wenn König und Turm auf Ausgangsfeld stehen und Felder dazwischen frei => Rochade bis jetzt möglich
	if color == "White" and board.loc["1","e"] == "wk" and board.loc["1","f"] == "--" and board.loc["1","g"] == "--" and board.loc["1","h"] == "wr":
		# Wenn König oder Turm schon bewegt wurden => Rochade nicht möglich
		for move in moveHistory:
			if move[1] == "e1" or move[1] == "h1" or move[2] == "h1":
				return False
		# Wenn auch König und Turm noch nicht bewegt wurden => Rochade möglich
		return True

	# Prüfe Recht für kurze Rochade schwarz
	if color=="Black" and board.loc["8","e"]=="bk" and board.loc["8","f"]=="--" and board.loc["8","g"]=="--" and board.loc["8","h"]=="br":
		for move in moveHistory:
			if move[1]=="e8" or move[1]=="h8" or move[2]=="h8":
				return False
		return True

	return False


def checkLongCastleRight(color,moveHistory) -> bool:
	# Prüfe Recht für lange Rochade weiß
	if color=="White" and board.loc["1","a"]=="wr" and board.loc["1","b"]=="--" and board.loc["1","c"]=="--" and board.loc["1","d"]=="--" and board.loc["1","e"]=="wk":
		for move in moveHistory:
			if move[1]=="a1" or move[2]=="a1" or move[1]=="e1":
				return False
		return True

	# Prüfe Recht für lange Rochade schwarz
	if color=="Black" and board.loc["8","a"]=="br" and board.loc["8","b"]=="--" and board.loc["8","c"]=="--" and board.loc["8","d"]=="--" and board.loc["8","e"]=="bk":
		for move in moveHistory:
			if move[1]=="a8" or move[2]=="a8" or move[1]=="e8":
				return False
		return True

	return False


def checkCastleMovesV1(color,isMyKingInCheck,piece,legalMovesV1,moveHistory) -> tuple:
	shortCastleRight 	= checkShortCastleRight(color,moveHistory)
	longCastleRight 	= checkLongCastleRight(color,moveHistory)

	# König darf nicht im Schach stehen
	if not isMyKingInCheck:
		# Wenn König zieht
		if piece == "wk":
			# kurze Rochade weiß
			if shortCastleRight:
				legalMovesV1.append([7,6])
				legalMovesV1.append([7,7])
			# lange Rochade weiß
			if longCastleRight:
				legalMovesV1.append([7,0])
				legalMovesV1.append([7,2])
		if piece == "bk":	
			# kurze Rochade schwarz
			if shortCastleRight:
				legalMovesV1.append([0,6])
				legalMovesV1.append([0,7])
			# lange Rochade schwarz
			if longCastleRight:
				legalMovesV1.append([0,0])
				legalMovesV1.append([0,2])

	return legalMovesV1, shortCastleRight, longCastleRight

# ====================================================================================================
# Filtere legale Zugmöglichkeiten
# ====================================================================================================

def checkLegalMovesV1(color,piece,legalMovesV1,sourceSquareRank,sourceSquareLine,capturableEnPassant) -> list:

	if piece == "wp":
		legalMovesV1  = checkLegalMovesWhitePawn(legalMovesV1,sourceSquareRank,sourceSquareLine,capturableEnPassant)

	if piece == "bp":
		legalMovesV1  = checkLegalMovesBlackPawn(legalMovesV1,sourceSquareRank,sourceSquareLine,capturableEnPassant)

	if piece in ["wr","wb","wq","br","bb","bq"]:
		legalMovesV1  = checkLegalMovesRookBishopQueen(piece,legalMovesV1,sourceSquareRank,sourceSquareLine)

	if piece.endswith("n"):
		legalMovesV1  = checkLegalMovesKnight(piece,legalMovesV1,sourceSquareRank,sourceSquareLine)

	if piece.endswith("k"):
		legalMovesV1  = checkLegalMovesKing(piece,legalMovesV1,sourceSquareRank,sourceSquareLine)

	return legalMovesV1


def checkLegalMovesV2(color,piece,legalMovesV1,legalMovesV3,sourceSquareRank,sourceSquareLine) -> list:
	# call-by-value, daher copy
	legalMovesV4 = copy.copy(legalMovesV1)

	# "checkCastleMovesV2"
	# Prüfung, ob Rochadezug vorliegt und ob diese durchgeführt werden kann (König darf nicht ins Schach)
	for move in legalMovesV1:
		# kurze Rochade weiß
		# Beide Rochadezüge (man gibt als Zielfeld neues Königsfeld oder Turmfeld an) werden geprüft
		# Bei beiden Rochadezügen gilt: Die beiden Felder neben König (Zwischen- und Zielfeld) dürfen nicht bedroht sein
		if piece == "wk" and board.iloc[7,4] == "wk" and move in [[7,6],[7,7]]:
			# 1. Königsschritt gehen (Zwischenschritt)
			board.iloc[7,4] = "--"
			board.iloc[7,5] = "wk"
			# Wenn König im Schach
			if checkIfKingInCheck(color):
				# Dann Rochadezug entfernen
				legalMovesV4.remove(move)
				# Ausgangsstellung wiederherstellen
				board.iloc[7,5] = "--"
				board.iloc[7,4] = "wk"
				# Und nächster Zug
				continue
			# Wenn König nach 1. Königsschritt nicht im Schach
			else:
				# 2. Königsschritt gehen (Zielfeld)
				board.iloc[7,5] = "--"
				board.iloc[7,6] = "wk"
				# Wenn König im Schach
				if checkIfKingInCheck(color):
					# Dann Rochadezug entfernen
					legalMovesV4.remove(move)
					# Ausgangsstellung wiederherstellen
					board.iloc[7,6] = "--"
					board.iloc[7,4] = "wk"
					# Und nächster Zug
					continue
				# Wenn König auch nach 2. Königsschritt nicht im Schach
				else:
					# Ausgangsstellung wiederherstellen
					board.iloc[7,6] = "--"
					board.iloc[7,4] = "wk"
					# Wenn bei Rochade der Turm als Zielfeld gewählt wurde, soll das auch dann möglich sein, wenn das Turmfeld bedroht ist
					# Denn der König steht ja am Ende gar nicht auf dem Turmfeld
					# Ohne continue würde das abgelehnt werden, weil dann danach gerpüft wird, ob Turmfeld im Schach steht
					if move == [7,7]: continue

		# lange Rochade weiß
		if piece == "wk" and board.iloc[7,4] == "wk" and move in [[7,2],[7,0]]:
			board.iloc[7,4] = "--"
			board.iloc[7,3] = "wk"
			if checkIfKingInCheck(color):
				legalMovesV4.remove(move)
				board.iloc[7,3] = "--"
				board.iloc[7,4] = "wk"
				continue
			else:
				board.iloc[7,3] = "--"
				board.iloc[7,2] = "wk"
				if checkIfKingInCheck(color):
					legalMovesV4.remove(move)
					board.iloc[7,2] = "--"
					board.iloc[7,4] = "wk"
					continue
				else:
					board.iloc[7,2] = "--"
					board.iloc[7,4] = "wk"
					if move == [7,0]: continue

		# kurze Rochade schwarz
		if piece == "bk" and board.iloc[0,4] == "bk" and move in [[0,6],[0,7]]:
			board.iloc[0,4] = "--"
			board.iloc[0,5] = "bk"
			if checkIfKingInCheck(color):
				legalMovesV4.remove(move)
				board.iloc[0,5] = "--"
				board.iloc[0,4] = "bk"
				continue
			else:
				board.iloc[0,5] = "--"
				board.iloc[0,6] = "bk"
				if checkIfKingInCheck(color):
					legalMovesV4.remove(move)
					board.iloc[0,6] = "--"
					board.iloc[0,4] = "bk"
					continue
				else:
					board.iloc[0,6] = "--"
					board.iloc[0,4] = "bk"
					if move == [0,7]: continue

		# lange Rochade schwarz
		if piece == "bk" and board.iloc[0,4] == "bk" and move in [[0,2],[0,0]]:
			board.iloc[0,4] = "--"
			board.iloc[0,3] = "bk"
			if checkIfKingInCheck(color):
				legalMovesV4.remove(move)
				board.iloc[0,3] = "--"
				board.iloc[0,4] = "bk"
				continue
			else:
				board.iloc[0,3] = "--"
				board.iloc[0,2] = "bk"
				if checkIfKingInCheck(color):
					legalMovesV4.remove(move)
					board.iloc[0,2] = "--"
					board.iloc[0,4] = "bk"
					continue
				else:
					board.iloc[0,2] = "--"
					board.iloc[0,4] = "bk"
					if move == [0,0]: continue

		# Inhalt von Zielfeld zwischenspeichern, um move später zu resetten
		enterSquare = board.iloc[move[0],move[1]]

		# Zug ausführen (Quellfeld = "--" und Zielfeld = die gewählte Figur)
		board.iloc[sourceSquareRank,sourceSquareLine] = "--"
		board.iloc[move[0],move[1]] = piece

		# Wenn mein König nach dem getesteten legalMove im Schach steht, wird dieser Zug entfernt
		if checkIfKingInCheck(color):
			legalMovesV4.remove(move)

		# Nach der Prüfung wird der Zug wieder zurückgenommen (Zielfeld = die Figur, die vorher da stand und Quellfeld = die gewählte Figur)
		board.iloc[move[0],move[1]] = enterSquare
		board.iloc[sourceSquareRank,sourceSquareLine] = piece

	for lmv4 in legalMovesV4:
		legalMovesV3.append(lmv4)

	return legalMovesV3


def checkLegalMovesWhitePawn(legalMovesV1,sourceSquareRank,sourceSquareLine,capturableEnPassant) -> list:
	# Wenn Bauer in 2. Reihe
	if sourceSquareRank == 6:
		# Wenn Feld davor frei => füge Zug hinzu
		if board.iloc[sourceSquareRank-1,sourceSquareLine] == "--":
			legalMovesV1.append([sourceSquareRank-1,sourceSquareLine])
			# Wenn beide Felder davor frei => füge Zug hinzu
			if board.iloc[sourceSquareRank-2,sourceSquareLine] == "--":
				legalMovesV1.append([sourceSquareRank-2,sourceSquareLine])
		# Wenn wir nicht linke Spalte sind => prüfe Schlagzug nach links
		if sourceSquareLine != 0:
			# Wenn links oben Figur des Gegners steht => füge Zug hinzu
			if board.iloc[sourceSquareRank-1,sourceSquareLine-1].startswith("b"):
				legalMovesV1.append([sourceSquareRank-1,sourceSquareLine-1])
		# Wenn wir nicht rechte Spalte sind => prüfe Schlagzug nach rechts
		if sourceSquareLine != 7:
			# Wenn rechts oben Figur des Gegners steht => füge Zug hinzu
			if board.iloc[sourceSquareRank-1,sourceSquareLine+1].startswith("b"):
				legalMovesV1.append([sourceSquareRank-1,sourceSquareLine+1])

	# Wenn Bauer in 3./4./6./7. Reihe
	elif sourceSquareRank in [5,4,2,1]:
		# Wenn Feld davor frei => füge Zug hinzu
		if board.iloc[sourceSquareRank-1,sourceSquareLine] == "--":
			legalMovesV1.append([sourceSquareRank-1,sourceSquareLine])
		# Wenn wir nicht linke Spalte sind => prüfe Schlagzug nach links
		if sourceSquareLine != 0:
			# Wenn links oben Figur des Gegners steht => füge Zug hinzu
			if board.iloc[sourceSquareRank-1,sourceSquareLine-1].startswith("b"):
				legalMovesV1.append([sourceSquareRank-1,sourceSquareLine-1])
		# Wenn wir nicht rechte Spalte sind => prüfe Schlagzug nach rechts
		if sourceSquareLine != 7:
			# Wenn rechts oben Figur des Gegners steht => füge Zug hinzu
			if board.iloc[sourceSquareRank-1,sourceSquareLine+1].startswith("b"):
				legalMovesV1.append([sourceSquareRank-1,sourceSquareLine+1])

	# Wenn Bauer in 5. Reihe
	elif sourceSquareRank == 3:
		# Wenn Feld davor frei => füge Zug hinzu
		if board.iloc[sourceSquareRank-1,sourceSquareLine] == "--":
			legalMovesV1.append([sourceSquareRank-1,sourceSquareLine])
		# Wenn wir nicht linke Spalte sind => prüfe Schlagzug nach links
		if sourceSquareLine != 0:
			# Wenn links oben Figur des Gegners steht => füge Zug hinzu
			if board.iloc[sourceSquareRank-1,sourceSquareLine-1].startswith("b"):
				legalMovesV1.append([sourceSquareRank-1,sourceSquareLine-1])
			# Wenn links neben mir ein gegnerischer Bauer steht, der gerade einen Doppelschritt gegangen ist => füge Zug hinzu
			elif capturableEnPassant == [sourceSquareRank,sourceSquareLine-1]:
				legalMovesV1.append([sourceSquareRank-1,sourceSquareLine-1])
		# Wenn wir nicht rechte Spalte sind => prüfe Schlagzug nach rechts
		if sourceSquareLine != 7:
			# Wenn rechts oben Figur des Gegners steht => füge Zug hinzu
			if board.iloc[sourceSquareRank-1,sourceSquareLine+1].startswith("b"):
				legalMovesV1.append([sourceSquareRank-1,sourceSquareLine+1])
			# Wenn rechts neben mir ein gegnerischer Bauer steht, der gerade einen Doppelschritt gegangen ist => füge Zug hinzu
			elif capturableEnPassant == [sourceSquareRank,sourceSquareLine+1]:
				legalMovesV1.append([sourceSquareRank-1,sourceSquareLine+1])

	return legalMovesV1


def checkLegalMovesBlackPawn(legalMovesV1,sourceSquareRank,sourceSquareLine,capturableEnPassant) -> list:
	if sourceSquareRank == 1:
		if board.iloc[sourceSquareRank+1,sourceSquareLine] == "--":
			legalMovesV1.append([sourceSquareRank+1,sourceSquareLine])
			if board.iloc[sourceSquareRank+2,sourceSquareLine] == "--":
				legalMovesV1.append([sourceSquareRank+2,sourceSquareLine])
		if sourceSquareLine != 7:
			if board.iloc[sourceSquareRank+1,sourceSquareLine+1].startswith("w"):
				legalMovesV1.append([sourceSquareRank+1,sourceSquareLine+1])
		if sourceSquareLine != 0:
			if board.iloc[sourceSquareRank+1,sourceSquareLine-1].startswith("w"):
				legalMovesV1.append([sourceSquareRank+1,sourceSquareLine-1])

	elif sourceSquareRank in [2,3,5,6]:
		if board.iloc[sourceSquareRank+1,sourceSquareLine] == "--":
			legalMovesV1.append([sourceSquareRank+1,sourceSquareLine])
		if sourceSquareLine != 7:
			if board.iloc[sourceSquareRank+1,sourceSquareLine+1].startswith("w"):
				legalMovesV1.append([sourceSquareRank+1,sourceSquareLine+1])
		if sourceSquareLine != 0:
			if board.iloc[sourceSquareRank+1,sourceSquareLine-1].startswith("w"):
				legalMovesV1.append([sourceSquareRank+1,sourceSquareLine-1])

	elif sourceSquareRank == 4:
		if board.iloc[sourceSquareRank+1,sourceSquareLine] == "--":
			legalMovesV1.append([sourceSquareRank+1,sourceSquareLine])
		if sourceSquareLine != 7:
			if board.iloc[sourceSquareRank+1,sourceSquareLine+1].startswith("w"):
				legalMovesV1.append([sourceSquareRank+1,sourceSquareLine+1])
			elif capturableEnPassant == [sourceSquareRank,sourceSquareLine+1]:
				legalMovesV1.append([sourceSquareRank+1,sourceSquareLine+1])
		if sourceSquareLine != 0:
			if board.iloc[sourceSquareRank+1,sourceSquareLine-1].startswith("w"):
				legalMovesV1.append([sourceSquareRank+1,sourceSquareLine-1])
			elif capturableEnPassant == [sourceSquareRank,sourceSquareLine-1]:
				legalMovesV1.append([sourceSquareRank+1,sourceSquareLine-1])

	return legalMovesV1


def checkLegalMovesRookBishopQueen(piece,legalMovesV1,sourceSquareRank,sourceSquareLine) -> list:
	# Turm und Läufer haben max. 4, Dame max. 8 Richtungen. Alle können maximal 7 Schritte gehen
	for direction in range(1,9):
		for step in range(1,8):

			# Default-Werte von 10 sorgen später für Abbruch der step-Loop, wenn kein legaler Schritt (von 1-7) gefunden wird
			# Wenn z.B. bei Turm die directions 5-8 oder bei Läufer die directions 1-4 dran sind, soll break folgen
			stepRank = 10
			stepLine = 10

			# Turm oder Dame
			if piece.endswith("r") or piece.endswith("q"):
				# Je nach Richtung werden die Indizes definiert
				# 1 = vorne, 2 = hinten, 3 = rechts, 4 = links
				if direction == 1:
					stepRank = step * -1
					stepLine = 0
				elif direction == 2:
					stepRank = step * +1
					stepLine = 0
				elif direction == 3:
					stepRank = 0
					stepLine = step * +1
				elif direction == 4:
					stepRank = 0
					stepLine = step * -1

			# Läufer oder Dame
			if piece.endswith("b") or piece.endswith("q"):
				# Je nach Richtung werden die Indizes definiert
				# 5 = vorne rechts, 6 = hinten links, 7 = hinten rechts, 8 = vorne links
				if direction == 5:
					stepRank = step * -1
					stepLine = step * +1
				elif direction == 6:
					stepRank = step * +1
					stepLine = step * -1
				elif direction == 7:
					stepRank = step * +1
					stepLine = step * +1
				elif direction == 8:
					stepRank = step * -1
					stepLine = step * -1

			# Wenn Index außerhalb des Feldes (es werden bis zu 7 Schritte in jede Richtung geprüft) => prüfe nächste Richtung (direction)
			if not ((0 <= sourceSquareRank+stepRank <= 7) and (0 <= sourceSquareLine+stepLine <= 7)): break

			# Wenn eigene Figur im Weg => prüfe nächste Richtung (direction)
			if board.iloc[sourceSquareRank+stepRank,sourceSquareLine+stepLine].startswith(piece[0]): break

			# Wenn Gegner im Weg => füge Zug hinzu => prüfe nächste Richtung (direction)
			if board.iloc[sourceSquareRank+stepRank,sourceSquareLine+stepLine].startswith(otherColor[piece[0]]):
				legalMovesV1.append([sourceSquareRank+stepRank,sourceSquareLine+stepLine])
				break

			# Wenn zu prüfendes Feld frei => füge Zug hinzu => prüfe nächstes Feld (step)
			if board.iloc[sourceSquareRank+stepRank,sourceSquareLine+stepLine] == "--":
				legalMovesV1.append([sourceSquareRank+stepRank,sourceSquareLine+stepLine])
				continue

	return legalMovesV1


def checkLegalMovesKnight(piece,legalMovesV1,sourceSquareRank,sourceSquareLine) -> list:
	# Ein Springer kann max. 8 Felder betreten
	for direction in range(1,9):
		stepRank = 10
		stepLine = 10
		# Oben oben rechts
		if direction == 1:
			stepRank = -2
			stepLine = +1
		# Oben rechts rechts
		elif direction == 2:
			stepRank = -1
			stepLine = +2
		# Unten rechts rechts
		elif direction == 3:
			stepRank = +1
			stepLine = +2
		# Unten unten rechts
		elif direction == 4:
			stepRank = +2
			stepLine = +1
		# Unten unten links
		elif direction == 5:
			stepRank = +2
			stepLine = -1
		# Unten links links
		elif direction == 6:
			stepRank = +1
			stepLine = -2
		# Oben links links
		elif direction == 7:
			stepRank = -1
			stepLine = -2
		# Oben oben links
		elif direction == 8:
			stepRank = -2
			stepLine = -1

		# Wenn Index außerhalb des Feldes (es wird bis zu 1 Schritt in jede Richtung geprüft) => prüfe nächste Richtung (direction)
		if not ((0 <= sourceSquareRank+stepRank <= 7) and (0 <= sourceSquareLine+stepLine <= 7)): continue

		# Wenn eigene Figur auf dem Feld => prüfe nächste Richtung (direction)
		if board.iloc[sourceSquareRank+stepRank,sourceSquareLine+stepLine].startswith(piece[0]): continue

		# Wenn Gegner auf dem Feld => füge Zug hinzu => prüfe nächste Richtung (direction)
		if board.iloc[sourceSquareRank+stepRank,sourceSquareLine+stepLine].startswith(otherColor[piece[0]]):
			legalMovesV1.append([sourceSquareRank+stepRank,sourceSquareLine+stepLine])
			continue

		# Wenn zu prüfendes Feld frei => füge Zug hinzu => prüfe nächste Richtung (direction)
		if board.iloc[sourceSquareRank+stepRank,sourceSquareLine+stepLine] == "--":
			legalMovesV1.append([sourceSquareRank+stepRank,sourceSquareLine+stepLine])
			continue

	return legalMovesV1


def checkLegalMovesKing(piece,legalMovesV1,sourceSquareRank,sourceSquareLine) -> list:
	# Ein König kann max. 8 Felder betreten
	for direction in range(1,9):
		stepRank = 10
		stepLine = 10
		# oben
		if direction == 1:
			stepRank = -1
			stepLine = 0
		# oben rechts
		elif direction == 2:
			stepRank = -1
			stepLine = +1
		# rechts
		elif direction == 3:
			stepRank = 0
			stepLine = +1
		# unten rechts
		elif direction == 4:
			stepRank = +1
			stepLine = +1
		# unten
		elif direction == 5:
			stepRank = +1
			stepLine = 0
		# unten links
		elif direction == 6:
			stepRank = +1
			stepLine = -1
		# links
		elif direction == 7:
			stepRank = 0
			stepLine = -1
		# oben links
		elif direction == 8:
			stepRank = -1
			stepLine = -1

		# Wenn Index außerhalb des Feldes (es werden bis zu 2 Schritte in jede Richtung geprüft) => prüfe nächste Richtung (direction)
		if not ((0 <= sourceSquareRank+stepRank <= 7) and (0 <= sourceSquareLine+stepLine <= 7)): continue

		# Wenn eigene Figur im Weg => prüfe nächste Richtung (direction)
		if board.iloc[sourceSquareRank+stepRank,sourceSquareLine+stepLine].startswith(piece[0]): continue

		# Wenn Gegner im Weg => füge Zug hinzu => prüfe nächste Richtung (direction)
		if board.iloc[sourceSquareRank+stepRank,sourceSquareLine+stepLine].startswith(otherColor[piece[0]]):
			legalMovesV1.append([sourceSquareRank+stepRank,sourceSquareLine+stepLine])
			continue

		# Wenn zu prüfendes Feld frei => füge Zug hinzu => prüfe nächste Richtung (direction)
		if board.iloc[sourceSquareRank+stepRank,sourceSquareLine+stepLine] == "--":
			legalMovesV1.append([sourceSquareRank+stepRank,sourceSquareLine+stepLine])
			continue

	return legalMovesV1

# ====================================================================================================
# Führe bestimmte Zugaktionen durch
# ====================================================================================================

def promote(piece,targetSquareRank,playerWhite,playerBlack) -> tuple:
	# Checke, ob Umwandlung stattgefunden hat und speichere die Information + die Figur
	promotion = False
	if piece.endswith("p") and targetSquareRank in [0,7]:
		if (playerWhite == "human" and piece[0] == "w") or (playerBlack == "human" and piece[0] == "b"):
			piece = piece[0] + input("\nPromote to:\nq (Queen)\nr (Rook)\nb (Bishop)\nn (Knight)\n")
		if (playerWhite == "engine" and piece[0] == "w") or (playerBlack == "engine" and piece[0] == "b"):
			print("\nPromote to:\nq (Queen)\nr (Rook)\nb (Bishop)\nn (Knight)\n")
			piece = piece[0] + random.choice(["q","r","b","n"])
			print(piece[1]+"\n")
		promotion = True
	return piece, promotion


def move(piece,shortCastleRight,longCastleRight,sourceSquareRank,sourceSquareLine,targetSquareRank,targetSquareLine,capturableEnPassant) -> bool:

	hasTakenPiece = False

	# kurze Rochade weiß
	if piece == "wk" and shortCastleRight and (targetSquareLine == 6 or targetSquareLine == 7):
		board.iloc[7,4] = "--"
		board.iloc[7,6] = "wk"
		board.iloc[7,7] = "--"
		board.iloc[7,5] = "wr"

	# lange Rochade weiß
	elif piece == "wk" and longCastleRight and (targetSquareLine == 0 or targetSquareLine == 2):
		board.iloc[7,4] = "--"
		board.iloc[7,2] = "wk"
		board.iloc[7,0] = "--"
		board.iloc[7,3] = "wr"

	# kurze Rochade schwarz
	elif piece == "bk" and shortCastleRight and (targetSquareLine == 6 or targetSquareLine == 7):
		board.iloc[0,4] = "--"
		board.iloc[0,6] = "bk"
		board.iloc[0,7] = "--"
		board.iloc[0,5] = "br"

	# lange Rochade schwarz
	elif piece == "bk" and longCastleRight and (targetSquareLine == 0 or targetSquareLine == 2):
		board.iloc[0,4] = "--"
		board.iloc[0,2] = "bk"
		board.iloc[0,0] = "--"
		board.iloc[0,3] = "br"

	else:
		# Jeder Zug, der keine Rochade ist. Altes Feld räumen, neues Feld mit gezogener Figur besetzen
		board.iloc[sourceSquareRank,sourceSquareLine] = "--"
		board.iloc[targetSquareRank,targetSquareLine] = piece

	# Wenn auf Zielfeld Gegner steht => Schlagzug
	if board.iloc[targetSquareRank,targetSquareLine][0] == otherColor[piece[0]]:
		hasTakenPiece = True

	# Wenn enPassant möglich war UND ich weißen Bauer hatte UND ich auf 5. Reihe stand UND Spalte Zielfeld war Spalte gegenerischer Bauer
	if len(capturableEnPassant) == 2 and  piece == "wp" and sourceSquareRank == 3 and targetSquareLine == capturableEnPassant[1]:
		# Dann gegenerischen Bauer eliminieren => Schlagzug
		board.iloc[capturableEnPassant[0],capturableEnPassant[1]] = "--"
		hasTakenPiece = True

	if len(capturableEnPassant) == 2 and  piece == "bp" and sourceSquareRank == 4 and targetSquareLine == capturableEnPassant[1]:
		board.iloc[capturableEnPassant[0],capturableEnPassant[1]] = "--"
		hasTakenPiece = True

	return hasTakenPiece


def checkIfWeDoubleSteppedPawn(piece,sourceSquareRank,targetSquareRank,targetSquareLine) -> list:
	# Checke, ob wir gerade einen Bauern mit Doppelschritt bewegt haben, der als Nächstes durch enPassant vom Gegner geschlagen werden kann
	capturableEnPassant = []
	if piece.endswith("p") and abs(targetSquareRank-sourceSquareRank) == 2:
		capturableEnPassant = [targetSquareRank,targetSquareLine]
	return capturableEnPassant


def attackedByOpponent(dangerFields,color,piece) -> bool:
	for df in dangerFields:
		if board.iloc[df[0],df[1]] == (otherColor[color[0].lower()] + piece[1]):
			return True


def isUnderAttack(color,mySquareRank,mySquareLine) -> bool:

	# Prinzip der Funktion:
	# Vom Standpunkt des Königs werden Bauern/Springer/Läufer/Turm/Damen/Königszüge gegangen (dangerFields)
	# Wenn in solch einem Feld die jeweilige gegnerische Figur steht => Figur angegriffen => return True; sonst return False

	# Bauer
	piece = color[0].lower()+"p"
	dangerFields = []

	if piece == "wp":
		# wenn Feld links oben innerhalb des Brettes
		if ((0 <= mySquareRank-1 <= 7) and (0 <= mySquareLine-1 <= 7)):
			# dann wird Feld gespeichert und später geprüft, ob da gegn. Bauer steht
			dangerFields.append([mySquareRank-1,mySquareLine-1])

		# rechts oben
		if ((0 <= mySquareRank-1 <= 7) and (0 <= mySquareLine+1 <= 7)):
			dangerFields.append([mySquareRank-1,mySquareLine+1])

	if piece == "bp":
		# links oben (aus Perspektive von schwarz)
		if ((0 <= mySquareRank+1 <= 7) and (0 <= mySquareLine+1 <= 7)):
			dangerFields.append([mySquareRank+1,mySquareLine+1])

		# rechts oben (aus Perspektive von schwarz)
		if ((0 <= mySquareRank+1 <= 7) and (0 <= mySquareLine-1 <= 7)):
			dangerFields.append([mySquareRank+1,mySquareLine-1])

	if attackedByOpponent(dangerFields,color,piece): return True

	# Turm
	piece = color[0].lower()+"r"
	dangerFields = []
	dangerFields = checkLegalMovesRookBishopQueen(piece,dangerFields,mySquareRank,mySquareLine)

	if attackedByOpponent(dangerFields,color,piece): return True

	# Läufer
	piece = color[0].lower()+"b"
	dangerFields = []
	dangerFields = checkLegalMovesRookBishopQueen(piece,dangerFields,mySquareRank,mySquareLine)
	
	if attackedByOpponent(dangerFields,color,piece): return True

	# Dame
	piece = color[0].lower()+"q"
	dangerFields = []
	dangerFields = checkLegalMovesRookBishopQueen(piece,dangerFields,mySquareRank,mySquareLine)
	
	if attackedByOpponent(dangerFields,color,piece): return True

	# Springer
	piece = color[0].lower()+"n"
	dangerFields = []
	dangerFields = checkLegalMovesKnight(piece,dangerFields,mySquareRank,mySquareLine)

	if attackedByOpponent(dangerFields,color,piece): return True

	# König
	piece = color[0].lower()+"k"
	dangerFields = []
	dangerFields = checkLegalMovesKing(piece,dangerFields,mySquareRank,mySquareLine)

	if attackedByOpponent(dangerFields,color,piece): return True

	return False

# ====================================================================================================
# Starte Spiel, Schwarz und Weiß sind abwechselnd dran
# ====================================================================================================

def selectPlayerType(playerColor) -> str:
	while True:
		playerType = input(f"\nplayer {playerColor}:\n h (human) \n e (engine)\n\n")
		if playerType == "h":
			return "human"
		elif playerType == "e":
			return "engine"


def startGame():
	# Zughstorie / Bauern, die der Ziehende enPassant schlagen kann / vom Gegner kontrollierte Felder / Weiß beginnt
	moveHistory 		= []
	capturableEnPassant = []
	color 				= "White"

	print("\nWelcome to my chess game!")

	# playerWhite = selectPlayerType("White")
	# playerBlack = selectPlayerType("Black")
	playerWhite = "human"
	playerBlack = "human"

	print(board)

	while True:
		# Vor jedem Zug Schachgebot auf eigenen König prüfen / Vor jedem Zug Remis- oder Mattstellung prüfen
		isMyKingInCheck = checkIfKingInCheck(color)
		checkDrawCheckmate(color,moveHistory,boardCompositions,isMyKingInCheck,capturableEnPassant)

		print("\n"+color+" to move:")
		while True:
			if (playerWhite == "human" and color == "White") or (playerBlack == "human" and color == "Black"):
				sourceSquare = input("From: ")
			if (playerWhite == "engine" and color == "White") or (playerBlack == "engine" and color == "Black"):
				sourceSquare = LETTERS[random.randint(0,7)]+NUMBERS[random.randint(0,7)]

			# Eingabe muss aus zwei Zeichen bestehen: 1. Zeichen a-h und 2. Zeichen 1-8
			if len(sourceSquare) != 2 or sourceSquare[0] not in LETTERS or sourceSquare[1] not in NUMBERS: continue

			# Definition Funktionsparameter
			piece 				= board.loc[sourceSquare[1],sourceSquare[0]]	# Figur auf "From"-Feld, z.B. "wp" oder "bp"s
			sourceSquareRank 	= int(NUMBERS.index(sourceSquare[1]))			# Zahl/Reihe in Indexform [0-7]
			sourceSquareLine 	= int(LETTERS.index(sourceSquare[0]))			# Buchstabe/Linie in Indexform [0-7]

			# Wenn Farbe am Zug != Farbe der zu bewegenden Figur
			if piece[0] != color[0].lower(): continue

			# Prüfe Züge ohne Beachtung von Schach / ggf. füge Rochadezüge hinzu ohne Beachtung von Schach / ggf. entferne Züge, bei denen der König danach im Schach stehen würde
			legalMovesV1 		= []
			legalMovesV1 		= checkLegalMovesV1(color,piece,legalMovesV1,sourceSquareRank,sourceSquareLine,capturableEnPassant)	
			legalMovesV1,\
			shortCastleRight,\
			longCastleRight 	= checkCastleMovesV1(color,isMyKingInCheck,piece,legalMovesV1,moveHistory)
			legalMovesV3 		= []
			legalMovesV2 		= checkLegalMovesV2(color,piece,legalMovesV1,legalMovesV3,sourceSquareRank,sourceSquareLine)

			# Weiter gehts nur, wenn legaler Zug mit der Figur möglich, sonst Wdh. Eingabe (break)
			if legalMovesV2:
				# Bei Maschine wird gewähltes Feld jetzt ausgegeben, also erst nachdem legales Feld gefunden wurde
				if (playerWhite == "engine" and color == "White") or (playerBlack == "engine" and color == "Black"):
					print("From:",sourceSquare)
				break

		while True:
			if (playerWhite == "human" and color == "White") or (playerBlack == "human" and color == "Black"):
				targetSquare = input("To: ")
			if (playerWhite == "engine" and color == "White") or (playerBlack == "engine" and color == "Black"):
				targetSquare = LETTERS[random.randint(0,7)]+NUMBERS[random.randint(0,7)]

			# Eingabe muss aus zwei Zeichen bestehen: 1. Zeichen a-h und 1. Zeichen 1-8
			if len(targetSquare) != 2 or targetSquare[0] not in LETTERS or targetSquare[1] not in NUMBERS: continue

			# Defintion Prüfparameter
			targetSquareRank 	= int(NUMBERS.index(targetSquare[1]))
			targetSquareLine 	= int(LETTERS.index(targetSquare[0]))

			# Wiederholung Eingabe, wenn Zielfeld nicht legal
			if [targetSquareRank,targetSquareLine] not in legalMovesV2: continue

			# Bei Maschine wird gewähltes Feld jetzt ausgegeben, also erst nachdem legales Feld gefunden wurde
			if (playerWhite == "engine" and color == "White") or (playerBlack == "engine" and color == "Black"):
				print("To:",targetSquare)

			# ggf. umwandeln / ggf. enPassant geschlagenen Bauern eliminieren / immer Figur ziehen / ggf. gegangenen Doppelschritt merken / Zughistorie
			piece, promotion 	= promote(piece,targetSquareRank,playerWhite,playerBlack)
			hasTakenPiece 		= move(piece,shortCastleRight,longCastleRight,sourceSquareRank,sourceSquareLine,targetSquareRank,targetSquareLine,capturableEnPassant)
			capturableEnPassant = checkIfWeDoubleSteppedPawn(piece,sourceSquareRank,targetSquareRank,targetSquareLine)
			moveHistory.append([piece,sourceSquare,targetSquare,hasTakenPiece,promotion])

			break

		print()
		print(board)

		# Farbe wechseln
		color = "White" if color == "Black" else "Black"

		# board = flipBoard(color,board.values.tolist())
		# time.sleep(1)
		# print(board)

if __name__=="__main__":
	startGame()