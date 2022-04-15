word_place = open("test.txt")
word = str(word_place.read())


character_array = []

for w in word:
    character_array.append(w)

print(character_array)

character_array_2 = list(word)

print (character_array_2)


