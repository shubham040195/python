import sys
with open(sys.argv[1], 'r') as file:
     l1=[]
     for word in file:
	 for i in range(len(word)):
		char=word[i]
	        l1.append(char)
          
     print len(l1)
