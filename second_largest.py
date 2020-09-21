def find_second_largest(arrary):
	first_max = 0
	for i in arrary:
		if i > first_max:
			first_max = i
	return first_max

x=find_second_largest([1,2,3,4,5])
print x
