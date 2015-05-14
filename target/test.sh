echo "starting players"
for i in 1 2 3 4 5 6 7 8
do
    ./game 127.0.0.1 6000 127.0.0.$i 600$i $i$i$i$i
done
