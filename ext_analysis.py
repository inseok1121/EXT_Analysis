# -*- coding:CP949 -*-
from struct import *
import sys
import math

ReservedInode = {'.', '..', 'lost_found'}

p2 = lambda x, y : pack_from('<H', x, y)
up1 = lambda x, y : unpack_from('@c', x, y)[0]
up2 = lambda x, y : unpack_from('<H', x, y)[0]
up4 = lambda x, y : unpack_from('<L', x, y)[0]


	

if len(sys.argv) > 2 :
	print ("python3 ",sys.argv[0],"  <FILE NAME>")
	sys.exit(1)
elif len(sys.argv) == 1:
	print ("python3 ",sys.argv[0],"  <FILE NAME>")
	sys.exit(1)

f = open(sys.argv[1], 'rb')

f.seek(1024)
superblock = f.read(1024)

print ("[*]Super Block # ================================")

Signature = up2(superblock, 0x38)
print ('Magic Signature : ', hex(Signature))

CountInode = up4(superblock, 0x00)
print ('Count of Inodes : ', CountInode)

CountBlock = up4(superblock, 0x04)
print ('Count of Blocks : ', CountBlock)

CountFreeInode = up4(superblock, 0x14)
print ('Count of Free Inode : ', CountFreeInode)

BlockSize = up4(superblock, 0x18)
BlockSize = pow(2, 10+BlockSize)
print ('Block size : ', BlockSize)

BlocksPGroup = up4(superblock, 0x20)
print ('Blocks Per Group : ', BlocksPGroup)

InodesPGroup = up4(superblock, 0x28)
print ('Inodes Per Group : ', InodesPGroup)

NumofGroupbyB = math.ceil(CountBlock / BlocksPGroup)
print ('Number of Block Group by Block : ', NumofGroupbyB)

NumofGroupbyI = math.ceil(CountInode / InodesPGroup)
print ('Number of Bloack Group by Inode : ', NumofGroupbyI)


SizeGDTEntry = up2(superblock, 0xFE)
if SizeGDTEntry == 0:
	SizeGDTEntry = 32
print ('Size of GDT Entry : ', SizeGDTEntry)

########################################
##############GDT#######################
########################################


if BlockSize != 1024 :
	f.seek(BlockSize)
else :
	f.seek(2048)
gdt = f.read(SizeGDTEntry)
print ("[*]GTD # ======================================")
##	BlockAdd = up4(gdt, 0x00)
##	print ('Start of Block Bitmap Address : ', BlockAdd)

##	InodeAdd = up4(gdt, 0x04)
##	print ('Start of Inode Bitmap Address : ', InodeAdd)
	
InodetableAdd = up4(gdt, 0x08)
print ('Root Directory Inode Table Address : ', InodetableAdd)

RootEntry = InodetableAdd * BlockSize
f.seek(RootEntry+256)
inode = f.read(4096)

RootDirectory = up4(inode, 0x28)
INODE = RootDirectory * BlockSize

def GoingInode(add, TargetIndex):
	f.seek(add+(TargetIndex*256))
	checkdir = f.read(2)
	

	if checkdir[1] == 65 :
		temp = f.read(254)
		nextdir = up4(temp, 0x26)
		nextdiradd = nextdir * BlockSize
		print ("<*>Directory<*>")
		GoingDeep(nextdiradd)
	else:
		temp = f.read(254)
		filesize = up4(temp, 0x02)
		print ("<*>File<*>")
		print ("File Size :",filesize)

		i = 0x00
		print ("Block Pointer :")
		while(i<=44):
			###0~11 Direct###
			blockpt = up4(temp, 0x26+i)
			if blockpt == 0x00000000 :
				break
			print ("	",blockpt)
			
			i = i+4
		####12 Indirect####
		blockpt = up4(temp, 0x56)
		if blockpt != 0x00000000 :
			j = 0x00
			f.seek(blockpt * BlockSize)
			indirect = f.read(BlockSize)
			while(j<BlockSize):
				blockpt = up4(indirect, 0x00+j)
				if blockpt == 0x00000000 :
					break
				print("		", blockpt)
				j = j+4

				
		####13 Double Indirect####
		blockpt = up4(temp, 0x5A)	
		if blockpt != 0x00000000 :
			j = 0x00
			f.seek(blockpt * BlockSize)
			indirect = f.read(BlockSize)
			while(j<BlockSize):
				blockpt = up4(indirect, 0x00+j)
				if blockpt != 0x00000000 :
					k = 0x00
					f.seek(blockpt * BlockSize)
					doubleindirect = f.read(BlockSize)
					while(k<BlockSize):
						blockpt = up4(doubleindirect, 0x00+k)
						if blockpt == 0x00000000:
							break
						print("			",blockpt)
						k = k+4
				else :
					break
				j = j+4
		####14 Triple Indirect####
		blockpt = up4(temp, 0x5E)
		if blockpt != 00000000:
			i = 0x00
			f.seek(blockpt*BlockSize)
			indirect = f.read(BlockSize)
			while(j<BlockSize):
				blockpt = up4(indirect, 0x00+j)
				if blockpt != 0x00000000 :
					j = 0x00
					f.seek(blockpt*BlockSize)
					doubleindirect = f.read(BlockSize)
					while(k<BlockSize):
						blockpt=up4(doubleindirect, 0x00+j)
						if blockpt != 0x00000000:
							k = 0x00
							f.seek(blockpt+BlockSize)
							ddindirect = f.read(BlockSize)
							while(k<BlockSize):
								blockpt = up4(ddindirect, 0x00+k)
								if blockpt == 0x00000000:
									break
								print("			",blockpt)
								k = k+4
						else:
							break
						k = k+4
				else:
					break
				j = j+4
		print()


def GoingGDT(add):
	TargetEntry = int((add-1)/InodesPGroup)
	TargetIndex = int((add-1)%InodesPGroup)
	if BlockSize != 1024 :
		f.seek(BlockSize+(SizeGDTEntry * (TargetEntry)))
	else :
		f.seek(2048+(SizeGDTEntry * (TargetEntry)))
	
	temp = f.read(SizeGDTEntry)	
	TargetInode = up4(temp, 0x08)
	NextDirectory = TargetInode * BlockSize
	GoingInode(NextDirectory, TargetIndex)

def GoingDeep(add):
	
	f.seek(add)
	temp = f.read(4)
	numofInode = up4(temp, 0x00)
	if numofInode == 0x00 :
		return

	f.seek(add+6)
	temp = f.read(1)
	Namelen = ord(temp)
	inode = add+8
	f.seek(inode)
	name = f.read(Namelen)

	if Namelen%4 == 0:
		Namelen = Namelen
	else:
		Namelen = int((int((Namelen/4))+1)*4)


	
	if name == b'.' or name == b'..' :
		Name = name.decode('unicode-escape')
		print (Name)
		nextinode = add+8+Namelen
		GoingDeep(nextinode)
	else:
		Name = name.decode('unicode-escape')
		print()
		print (Name)
		GoingGDT(numofInode)
		nextinode = add+8+Namelen
		GoingDeep(nextinode)

	return
		
GoingDeep(INODE)