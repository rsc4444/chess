import copy
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
# Prüfe bestimmte Zustände
# ====================================================================================================

def checkDrawCheckmate(color,moveHistory,boardCompositions,myKingInCheck,capturableEnPassant):
	totalValuePieces 	= 0
	lightSquaredBishops = 0
	darkSquaredBishops 	= 0
	legalMovesV3 		= []
	fiftyMovesDraw 		= False

	boardComposition = board.values.tolist()
	boardCompositions.append(boardComposition)

	if boardCompositions.count(boardComposition) == 3:
		sys.exit("Threefold repetition! This is a draw.")

	# Alle 64 Felder durchgehen und (Figuren)werte zählen für Remisprüfung durch zu wenig Material
	# Alle 64 Felder durchgehen und legale Züge speichern für Patt- und Mattprüfung
	for sqr in range(8):
		for sql in range(8):
			piece = board.iloc[sqr,sql]
			# p = pawn (Bauer), q = queen (Dame), r = rook (Turm), n = knight (Springer), b = bishop (Läufer)
			if piece[1] == "p" or piece[1] == "q" or piece[1] == "r":
				totalValuePieces += 9
			elif piece[1] == "n":
				totalValuePieces += 3
			elif piece[1] == "b":
				totalValuePieces += 3
				# Zeilen- und Spaltenindex 2x gerade oder 2x ungerade => weißes Feld
				if (sqr % 2) == (sql % 2):
					lightSquaredBishops += 1
				# Zeilen- und Spaltenindex 1x gerade und 1x ungerade => schwarzes Feld
				elif (sqr % 2) != (sql % 2):
					darkSquaredBishops += 1

			# Wenn piece = eigene Figur
			if (piece[0] == color[0].lower()):
				legalMovesV1 = []
				legalMovesV1 = checkLegalMovesV1(piece,legalMovesV1,sqr,sql,capturableEnPassant)
				legalMovesV2 = checkLegalMovesV2(color,piece,legalMovesV1,legalMovesV3,sqr,sql)

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
		if not myKingInCheck:
			sys.exit("\nStalemate! This is a draw.\n")
		# ...und König im Schach => Matt
		if myKingInCheck:
			color = "White" if color == "Black" else "Black"
			sys.exit("\nCheckmate! "+color+" wins.\n")

	if fiftyMovesDraw:
		sys.exit("\n50 moves without moving a pawn, taking a piece or mating the king! This is a draw.\n")


def isMyKingInCheck(color) -> bool:
	# Iteration über das Brett. Feld mit eigenem König wird gesucht
	for sqr in range(8):
		for sql in range(8):
			# Wenn eigener König gefunden => prüfe, ob dieser im Schach steht (return True/False)
			if board.iloc[sqr,sql] == color[0].lower()+"k":
				return isUnderAttack(color,sqr,sql)


def checkShortCastleRight(color,moveHistory) -> bool:
	# Wenn König und Turm auf Ausgangsfeld stehen und Felder dazwischen frei => Rochade bis jetzt möglich
	if color == "White" and board.loc["1","e"] == "wk" and board.loc["1","f"] == "--" and board.loc["1","g"] == "--" and board.loc["1","h"] == "wr":
		# Wenn König oder Turm schon bewegt wurden => Rochade nicht möglich, sonst schon
		for move in moveHistory:
			if move[1] == "e1" or move[1] == "h1" or move[2] == "h1":
				return False
		return True

	if color=="Black" and board.loc["8","e"]=="bk" and board.loc["8","f"]=="--" and board.loc["8","g"]=="--" and board.loc["8","h"]=="br":
		for move in moveHistory:
			if move[1]=="e8" or move[1]=="h8" or move[2]=="h8":
				return False
		return True

	return False


def checkLongCastleRight(color,moveHistory) -> bool:
	if color=="White" and board.loc["1","a"]=="wr" and board.loc["1","b"]=="--" and board.loc["1","c"]=="--" and board.loc["1","d"]=="--" and board.loc["1","e"]=="wk":
		for move in moveHistory:
			if move[1]=="a1" or move[2]=="a1" or move[1]=="e1":
				return False
		return True

	if color=="Black" and board.loc["8","a"]=="br" and board.loc["8","b"]=="--" and board.loc["8","c"]=="--" and board.loc["8","d"]=="--" and board.loc["8","e"]=="bk":
		for move in moveHistory:
			if move[1]=="a8" or move[2]=="a8" or move[1]=="e8":
				return False
		return True

	return False


def checkCastleMovesV1(color,myKingInCheck,piece,legalMovesV1,moveHistory) -> tuple:
	shortCastleRight 	= checkShortCastleRight(color,moveHistory)
	longCastleRight 	= checkLongCastleRight(color,moveHistory)

	# König darf nicht im Schach stehen und König muss am Zug sein => füge Rochadezüge hinzu
	if not myKingInCheck:
		if piece == "wk":
			if shortCastleRight:
				legalMovesV1.append([7,6])
				legalMovesV1.append([7,7])
			if longCastleRight:
				legalMovesV1.append([7,0])
				legalMovesV1.append([7,2])
		if piece == "bk":
			if shortCastleRight:
				legalMovesV1.append([0,6])
				legalMovesV1.append([0,7])
			if longCastleRight:
				legalMovesV1.append([0,0])
				legalMovesV1.append([0,2])

	return legalMovesV1, shortCastleRight, longCastleRight

# ====================================================================================================
# Filtere legale Zugmöglichkeiten
# ====================================================================================================

def checkLegalMovesV1(piece,legalMovesV1,sqr,sql,capturableEnPassant) -> list:
	if piece == "wp":
		legalMovesV1  = checkLegalMovesWhitePawn(legalMovesV1,sqr,sql,capturableEnPassant)

	if piece == "bp":
		legalMovesV1  = checkLegalMovesBlackPawn(legalMovesV1,sqr,sql,capturableEnPassant)

	if piece in ["wr","wb","wq","br","bb","bq"]:
		legalMovesV1  = checkLegalMovesRookBishopQueen(piece,legalMovesV1,sqr,sql)

	if piece.endswith("n"):
		legalMovesV1  = checkLegalMovesKnight(piece,legalMovesV1,sqr,sql)

	if piece.endswith("k"):
		legalMovesV1  = checkLegalMovesKing(piece,legalMovesV1,sqr,sql)

	return legalMovesV1


def checkLegalMovesV2(color,piece,legalMovesV1,legalMovesV3,sqr,sql) -> list:	
	legalMovesV4 = copy.copy(legalMovesV1) # call-by-value, daher copy

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
			# Wenn König im Schach => Rochadezug entfernen + Ausgangsstellung wiederherstellen + nächster Zug
			if isMyKingInCheck(color):
				legalMovesV4.remove(move)				
				board.iloc[7,5] = "--"
				board.iloc[7,4] = "wk"
				continue
			# Wenn König nach 1. Königsschritt nicht im Schach => 2. Königsschritt gehen (Zielfeld)
			else:
				board.iloc[7,5] = "--"
				board.iloc[7,6] = "wk"
				# Wenn König im Schach => Rochadezug entfernen + Ausgangsstellung wiederherstellen + nächster Zug
				if isMyKingInCheck(color):
					legalMovesV4.remove(move)
					board.iloc[7,6] = "--"
					board.iloc[7,4] = "wk"
					continue
				# Wenn König auch nach 2. Königsschritt nicht im Schach => Ausgangsstellung wiederherstellen
				else:
					board.iloc[7,6] = "--"
					board.iloc[7,4] = "wk"
					# Wenn bei Rochade der Turm als Zielfeld gewählt wurde, soll das auch dann möglich sein, wenn das Turmfeld bedroht ist
					# Ohne continue würde der Zug im Anshcluss removed werden, weil dann geprüft wird, ob Turmfeld im Schach steht
					if move == [7,7]: continue

		# lange Rochade weiß
		if piece == "wk" and board.iloc[7,4] == "wk" and move in [[7,2],[7,0]]:
			board.iloc[7,4] = "--"
			board.iloc[7,3] = "wk"
			if isMyKingInCheck(color):
				legalMovesV4.remove(move)
				board.iloc[7,3] = "--"
				board.iloc[7,4] = "wk"
				continue
			else:
				board.iloc[7,3] = "--"
				board.iloc[7,2] = "wk"
				if isMyKingInCheck(color):
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
			if isMyKingInCheck(color):
				legalMovesV4.remove(move)
				board.iloc[0,5] = "--"
				board.iloc[0,4] = "bk"
				continue
			else:
				board.iloc[0,5] = "--"
				board.iloc[0,6] = "bk"
				if isMyKingInCheck(color):
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
			if isMyKingInCheck(color):
				legalMovesV4.remove(move)
				board.iloc[0,3] = "--"
				board.iloc[0,4] = "bk"
				continue
			else:
				board.iloc[0,3] = "--"
				board.iloc[0,2] = "bk"
				if isMyKingInCheck(color):
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
		board.iloc[sqr,sql] = "--"
		board.iloc[move[0],move[1]] = piece

		# Wenn mein König nach dem getesteten legalMove im Schach steht, wird dieser Zug entfernt
		if isMyKingInCheck(color):
			legalMovesV4.remove(move)

		# Nach der Prüfung wird der Zug wieder zurückgenommen (Zielfeld = die Figur, die vorher da stand und Quellfeld = die gewählte Figur)
		board.iloc[move[0],move[1]] = enterSquare
		board.iloc[sqr,sql] = piece

	for lmv4 in legalMovesV4:
		legalMovesV3.append(lmv4)

	return legalMovesV3


def checkLegalMovesWhitePawn(legalMovesV1,sqr,sql,capturableEnPassant) -> list:
	# Wenn Bauer in 2. Reihe und beide Felder davor frei => füge Zug hinzu
	if sqr == 6 and board.iloc[sqr-1,sql] == "--" and board.iloc[sqr-2,sql] == "--":
		legalMovesV1.append([sqr-2,sql])
	# Wenn Bauer in 5. Reihe und links bzw. rechts neben mir ein gegnerischer Bauer steht
	# der gerade einen Doppelschritt gegangen ist => füge Zug hinzu
	elif sqr == 3 and sql != 0 and capturableEnPassant == [sqr,sql-1]:
		legalMovesV1.append([sqr-1,sql-1])
	elif sqr == 3 and sql != 7 and capturableEnPassant == [sqr,sql+1]:
		legalMovesV1.append([sqr-1,sql+1])
	# Immer und unabhängig von Reihe: Feld davor frei? Schlagzug nach links/rechts möglich?
	if board.iloc[sqr-1,sql] == "--":
		legalMovesV1.append([sqr-1,sql])
	if sql != 0 and board.iloc[sqr-1,sql-1].startswith("b"):
		legalMovesV1.append([sqr-1,sql-1])
	if sql != 7 and board.iloc[sqr-1,sql+1].startswith("b"):
		legalMovesV1.append([sqr-1,sql+1])
	return legalMovesV1


def checkLegalMovesBlackPawn(legalMovesV1,sqr,sql,capturableEnPassant) -> list:
	if sqr == 1 and board.iloc[sqr+1,sql] == "--" and board.iloc[sqr+2,sql] == "--":
		legalMovesV1.append([sqr+2,sql])			
	elif sqr == 4 and sql != 7 and capturableEnPassant == [sqr,sql+1]:
		legalMovesV1.append([sqr+1,sql+1])
	elif sqr == 4 and sql != 0 and capturableEnPassant == [sqr,sql-1]:
		legalMovesV1.append([sqr+1,sql-1])
	if board.iloc[sqr+1,sql] == "--":
		legalMovesV1.append([sqr+1,sql])
	if sql != 7 and board.iloc[sqr+1,sql+1].startswith("w"):
		legalMovesV1.append([sqr+1,sql+1])		
	if sql != 0 and board.iloc[sqr+1,sql-1].startswith("w"):
		legalMovesV1.append([sqr+1,sql-1])
	return legalMovesV1


def checkLegalMovesRookBishopQueen(piece,legalMovesV1,sqr,sql) -> list:
	# Turm und Läufer haben max. 4, Dame max. 8 Richtungen. Alle können maximal 7 Schritte gehen
	for direction in range(1,9):
		for step in range(1,8):

			# Default-Werte von 10 sorgen später für Abbruch der step-Loop, wenn kein legaler Schritt (von 1-7) gefunden wird
			# Wenn z.B. bei Turm die directions 5-8 oder bei Läufer die directions 1-4 dran sind, soll break folgen
			stepRank, stepLine = 10, 10
			
			if piece.endswith("r") or piece.endswith("q"): # Turm oder Dame
				# 1 = vorne, 2 = hinten, 3 = rechts, 4 = links
				if direction == 1:   # vorne
					stepRank, stepLine = step*-1, 0
				elif direction == 2: # hinten
					stepRank, stepLine = step*+1, 0
				elif direction == 3: # rechts
					stepRank, stepLine = 0, step*+1
				elif direction == 4: # links
					stepRank, stepLine = 0, step*-1
			
			if piece.endswith("b") or piece.endswith("q"): # Läufer oder Dame
				if direction == 5:  # vorne rechts
					stepRank, stepLine = step*-1, step*+1
				elif direction == 6: # hinten links
					stepRank, stepLine = step*+1, step*-1
				elif direction == 7: # hinten rechts
					stepRank, stepLine = step*+1, step*+1
				elif direction == 8: # vorne links
					stepRank, stepLine = step*-1, step*-1

			if not ((0 <= sqr+stepRank <= 7) and (0 <= sql+stepLine <= 7)): break #Index außerhalb => nächste Richtung

			if board.iloc[sqr+stepRank,sql+stepLine].startswith(piece[0]): break #Eigene Figur im Weg => nächste Richtung

			if board.iloc[sqr+stepRank,sql+stepLine].startswith(otherColor[piece[0]]): #Gegner im Weg => Zug hinzu + nächste Richtung
				legalMovesV1.append([sqr+stepRank,sql+stepLine])
				break

			if board.iloc[sqr+stepRank,sql+stepLine] == "--": #Feld frei => Zug hinzu + nächster Schritt
				legalMovesV1.append([sqr+stepRank,sql+stepLine])
				continue

	return legalMovesV1


def checkLegalMovesKnight(piece,legalMovesV1,sqr,sql) -> list:
	# Ein Springer kann max. 8 Felder betreten
	for direction in range(1,9):
		stepRank, stepLine = 10, 10		
		if direction == 1:   # oben oben rechts
			stepRank, stepLine = -2, +1		
		elif direction == 2: # oben rechts rechts
			stepRank, stepLine = -1, +2		
		elif direction == 3: # unten rechts rechts
			stepRank, stepLine = +1, +2		
		elif direction == 4: # unten unten rechts
			stepRank, stepLine = +2, +1		
		elif direction == 5: # unten unten links
			stepRank, stepLine = +2, -1		
		elif direction == 6: # unten links links
			stepRank, stepLine = +1, -2		
		elif direction == 7: # oben links links
			stepRank, stepLine = -1, -2		
		elif direction == 8: # oben oben links
			stepRank, stepLine = -2, -1

		if not ((0 <= sqr+stepRank <= 7) and (0 <= sql+stepLine <= 7)): continue #Index außerhalb => nächste Richtung

		if board.iloc[sqr+stepRank,sql+stepLine].startswith(piece[0]): continue #Eigene Figur im Weg => nächste Richtung

		if board.iloc[sqr+stepRank,sql+stepLine].startswith(otherColor[piece[0]]): #Gegner im Weg => Zug hinzu + nächste Richtung
			legalMovesV1.append([sqr+stepRank,sql+stepLine])
			continue

		if board.iloc[sqr+stepRank,sql+stepLine] == "--": #Feld frei => Zug hinzu + nächste Richtung
			legalMovesV1.append([sqr+stepRank,sql+stepLine])
			continue

	return legalMovesV1


def checkLegalMovesKing(piece,legalMovesV1,sqr,sql) -> list:
	# Ein König kann max. 8 Felder betreten
	for direction in range(1,9):
		stepRank, stepLine = 10, 10		
		if direction == 1:   # oben
			stepRank, stepLine = -1, 0		
		elif direction == 2: # oben rechts
			stepRank, stepLine = -1, +1		
		elif direction == 3: # rechts
			stepRank, stepLine = 0, +1		
		elif direction == 4: # unten rechts
			stepRank, stepLine = +1, +1		
		elif direction == 5: # unten
			stepRank, stepLine = +1, 0		
		elif direction == 6: # unten links
			stepRank, stepLine = +1, -1		
		elif direction == 7: # links
			stepRank, stepLine = 0, -1		
		elif direction == 8: # oben links
			stepRank, stepLine = -1, -1

		if not ((0 <= sqr+stepRank <= 7) and (0 <= sql+stepLine <= 7)): continue #Index außerhalb => nächste Richtung

		if board.iloc[sqr+stepRank,sql+stepLine].startswith(piece[0]): continue #Eigene Figur im Weg => nächste Richtung

		if board.iloc[sqr+stepRank,sql+stepLine].startswith(otherColor[piece[0]]): #Gegner im Weg => Zug hinzu + nächste Richtung
			legalMovesV1.append([sqr+stepRank,sql+stepLine])
			continue

		if board.iloc[sqr+stepRank,sql+stepLine] == "--": #Feld frei => Zug hinzu + nächste Richtung
			legalMovesV1.append([sqr+stepRank,sql+stepLine])
			continue

	return legalMovesV1

# ====================================================================================================
# Führe bestimmte Zugaktionen durch
# ====================================================================================================

def promote(piece,tsr,playerWhite,playerBlack) -> tuple:
	# Checke, ob Umwandlung stattgefunden hat und speichere die Information + die Figur
	promotion = False
	if piece.endswith("p") and tsr in [0,7]:
		if (playerWhite == "human" and piece[0] == "w") or (playerBlack == "human" and piece[0] == "b"):
			piece = piece[0] + input("\nPromote to:\nq (Queen)\nr (Rook)\nb (Bishop)\nn (Knight)\n")
		if (playerWhite == "engine" and piece[0] == "w") or (playerBlack == "engine" and piece[0] == "b"):
			print("\nPromote to:\nq (Queen)\nr (Rook)\nb (Bishop)\nn (Knight)\n")
			piece = piece[0] + random.choice(["q","r","b","n"])
			print(piece[1]+"\n")
		promotion = True
	return piece, promotion


def move(piece,shortCastleRight,longCastleRight,sqr,sql,tsr,tsl,capturableEnPassant) -> bool:
	hasTakenPiece = False

	# kurze Rochade weiß / lange Rochade weiß / kurze Rochade schwarz / lange Rochade schwarz
	if piece == "wk" and shortCastleRight and (tsl == 6 or tsl == 7):
		board.iloc[7,4] = "--"
		board.iloc[7,6] = "wk"
		board.iloc[7,7] = "--"
		board.iloc[7,5] = "wr"

	elif piece == "wk" and longCastleRight and (tsl == 0 or tsl == 2):
		board.iloc[7,4] = "--"
		board.iloc[7,2] = "wk"
		board.iloc[7,0] = "--"
		board.iloc[7,3] = "wr"

	elif piece == "bk" and shortCastleRight and (tsl == 6 or tsl == 7):
		board.iloc[0,4] = "--"
		board.iloc[0,6] = "bk"
		board.iloc[0,7] = "--"
		board.iloc[0,5] = "br"

	elif piece == "bk" and longCastleRight and (tsl == 0 or tsl == 2):
		board.iloc[0,4] = "--"
		board.iloc[0,2] = "bk"
		board.iloc[0,0] = "--"
		board.iloc[0,3] = "br"

	# Jeder Zug, der keine Rochade ist. Altes Feld räumen, neues Feld mit gezogener Figur besetzen
	else:
		board.iloc[sqr,sql] = "--"
		board.iloc[tsr,tsl] = piece

	# Wenn auf Zielfeld Gegner steht => Schlagzug
	if board.iloc[tsr,tsl][0] == otherColor[piece[0]]:
		hasTakenPiece = True

	# Wenn enPassant möglich war UND ich weißen Bauer hatte UND ich auf 5. Reihe stand UND Spalte Zielfeld war Spalte gegenerischer Bauer
	if len(capturableEnPassant) == 2 and  piece == "wp" and sqr == 3 and tsl == capturableEnPassant[1]:
		# Dann gegenerischen Bauer eliminieren => Schlagzug
		board.iloc[capturableEnPassant[0],capturableEnPassant[1]] = "--"
		hasTakenPiece = True

	if len(capturableEnPassant) == 2 and  piece == "bp" and sqr == 4 and tsl == capturableEnPassant[1]:
		board.iloc[capturableEnPassant[0],capturableEnPassant[1]] = "--"
		hasTakenPiece = True

	return hasTakenPiece


def checkIfWeDoubleSteppedPawn(piece,sqr,tsr,tsl) -> list:
	# Checke, ob wir gerade einen Bauern mit Doppelschritt bewegt haben, der als Nächstes durch enPassant vom Gegner geschlagen werden kann
	capturableEnPassant = []
	if piece.endswith("p") and abs(tsr-sqr) == 2:
		capturableEnPassant = [tsr,tsl]
	return capturableEnPassant


def attackedByOpponent(dangerFields,color,piece) -> bool:
	for df in dangerFields:
		if board.iloc[df[0],df[1]] == (otherColor[color[0].lower()] + piece[1]):
			return True


def isUnderAttack(color,mySquareRank,mySquareLine) -> bool:
	# Vom Standpunkt des Königs werden Bauern/Springer/Läufer/Turm/Damen/Königszüge gegangen (dangerFields)
	# Wenn in solch einem Feld die jeweilige gegnerische Figur steht => König angegriffen => return True; sonst return False

	piece = color[0].lower()+"p" # Bauer
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

	piece = color[0].lower()+"r" # Turm
	dangerFields = []
	dangerFields = checkLegalMovesRookBishopQueen(piece,dangerFields,mySquareRank,mySquareLine)
	if attackedByOpponent(dangerFields,color,piece): return True

	piece = color[0].lower()+"b" # Läufer
	dangerFields = []
	dangerFields = checkLegalMovesRookBishopQueen(piece,dangerFields,mySquareRank,mySquareLine)	
	if attackedByOpponent(dangerFields,color,piece): return True

	piece = color[0].lower()+"q" # Dame
	dangerFields = []
	dangerFields = checkLegalMovesRookBishopQueen(piece,dangerFields,mySquareRank,mySquareLine)	
	if attackedByOpponent(dangerFields,color,piece): return True

	piece = color[0].lower()+"n" # Springer
	dangerFields = []
	dangerFields = checkLegalMovesKnight(piece,dangerFields,mySquareRank,mySquareLine)
	if attackedByOpponent(dangerFields,color,piece): return True

	piece = color[0].lower()+"k" # König
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
	# Zughstorie / Bauern, die der Ziehende enPassant schlagen kann / Weiß beginnt
	moveHistory 		= []
	capturableEnPassant = []
	color 				= "White"

	print("\nWelcome to my chess game!")
	playerWhite = selectPlayerType("White")
	playerBlack = selectPlayerType("Black")
	print(board)

	while True:
		# Vor jedem Zug prüfen: Mein König im Schach? Remisstellung? Mattstellung?
		myKingInCheck = isMyKingInCheck(color)
		checkDrawCheckmate(color,moveHistory,boardCompositions,myKingInCheck,capturableEnPassant)

		print("\n"+color+" to move:")
		while True:
			if (playerWhite == "human" and color == "White") or (playerBlack == "human" and color == "Black"):
				sourceSquare = input("From: ")
			if (playerWhite == "engine" and color == "White") or (playerBlack == "engine" and color == "Black"):
				sourceSquare = LETTERS[random.randint(0,7)]+NUMBERS[random.randint(0,7)]

			# Eingabe muss aus zwei Zeichen bestehen: 1. Zeichen a-h und 2. Zeichen 1-8
			if len(sourceSquare) != 2 or sourceSquare[0] not in LETTERS or sourceSquare[1] not in NUMBERS: continue

			# Definition Funktionsparameter: sourceSquareRank / sourceSquareLines
			piece 	= board.loc[sourceSquare[1],sourceSquare[0]]	# Figur auf "From"-Feld, z.B. "wp" oder "bp"s
			sqr 	= int(NUMBERS.index(sourceSquare[1]))			# Zahl/Reihe in Indexform [0-7]
			sql 	= int(LETTERS.index(sourceSquare[0]))			# Buchstabe/Linie in Indexform [0-7]

			# Wenn Farbe am Zug != Farbe der zu bewegenden Figur
			if piece[0] != color[0].lower(): continue

			# Prüfe Züge ohne Beachtung von Schach / ggf. füge Rochadezüge hinzu ohne Beachtung von Schach / ggf. entferne Züge, bei denen der König danach im Schach stehen würde
			legalMovesV1 		= []
			legalMovesV1 		= checkLegalMovesV1(piece,legalMovesV1,sqr,sql,capturableEnPassant)	
			legalMovesV1,\
			shortCastleRight,\
			longCastleRight 	= checkCastleMovesV1(color,myKingInCheck,piece,legalMovesV1,moveHistory)
			legalMovesV3 		= []
			legalMovesV2 		= checkLegalMovesV2(color,piece,legalMovesV1,legalMovesV3,sqr,sql)

			# Weiter gehts nur, wenn legaler Zug mit der Figur möglich, sonst Wdh. Eingabe (break)
			if legalMovesV2:
				# Bei Engine wird gewähltes Feld jetzt ausgegeben, also erst nachdem legales Feld gefunden wurde
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

			# Defintion Prüfparameter: targetSquareRank / targetSquareLine
			tsr 	= int(NUMBERS.index(targetSquare[1]))
			tsl 	= int(LETTERS.index(targetSquare[0]))

			# Wiederholung Eingabe, wenn Zielfeld nicht legal
			if [tsr,tsl] not in legalMovesV2: continue

			# Bei Engine wird gewähltes Feld jetzt ausgegeben, also erst nachdem legales Feld gefunden wurde
			if (playerWhite == "engine" and color == "White") or (playerBlack == "engine" and color == "Black"):
				print("To:",targetSquare)

			# ggf. umwandeln / ggf. enPassant geschlagenen Bauern eliminieren / immer Figur ziehen / ggf. gegangenen Doppelschritt merken / Zughistorie
			piece, promotion 	= promote(piece,tsr,playerWhite,playerBlack)
			hasTakenPiece 		= move(piece,shortCastleRight,longCastleRight,sqr,sql,tsr,tsl,capturableEnPassant)
			capturableEnPassant = checkIfWeDoubleSteppedPawn(piece,sqr,tsr,tsl)
			moveHistory.append([piece,sourceSquare,targetSquare,hasTakenPiece,promotion])
			break

		print()
		print(board)
		
		color = "White" if color == "Black" else "Black" # Farbe wechseln

if __name__=="__main__":
	startGame()