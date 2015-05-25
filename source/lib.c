#include "tables.h"
#include "lib.h"
#include <string.h>
#include <stdio.h>
#include <time.h>
#include <stdlib.h>

#define MAX_TEST 10000
#define TOTAL_DECK 52

const char *byte_to_binary(int x)
{
    static char b[9];
    b[0] = '\0';

    int z;
    for (z = 128; z > 0; z >>= 1)
    {
        strcat(b, ((x & z) == z) ? "1" : "0");
    }

    return b;
}

void shuffle(card_t* deck, int num_cards){
    /*给剩余的牌洗牌
     * deck 是牌堆，
     * num_cards 是牌堆数量*/
    int i,j;
    card_t card;
    for(i=0; i<num_cards; i++){
        j = rand()%num_cards;
        card = deck[j];
        deck[j]= deck[i];
        deck[i] = card;
    }
}

int init_deck(card_t* deck, card_t taken){
    //生成除了已知的牌外的牌堆
    //deck 是牌堆
    //taken 是已知手牌的掩码
    int i=0,j=0;
    card_t c;
    //printf("%lx\n",taken);
    for(i=0; i<52; i++){
        c = 1L << i;
        if((c & taken) == 0){
            deck[j] = c;
            j += 1;
        }
        else{
            //printf("%d ",j);
            //printf("i %d \n",i);
        }
    }
    return j;
}

int score6(card_t c1, card_t c2, card_t c3, card_t c4, card_t c5, card_t c6){
    static int index[] = { 0, 1, 2, 3, 4, 
                           0, 1, 2, 3, 4, 6,
                           0, 1, 2, 3, 5, 6,
                           0, 1, 2, 4, 5, 6,
                           0, 1, 3, 4, 5, 6,
                           1, 2, 3, 4, 5, 6};
    card_t cards[6]; 
    int i,j;
    int max_score=0;
    int score;
    cards[0] = c1;
    cards[1] = c2;
    cards[2] = c3;
    cards[3] = c4;
    cards[4] = c5;
    cards[5] = c6;
    for(i=0; i<6; i++){
        score = score5(cards[index[5*i]], cards[index[5*i+1]], cards[index[5*i+2]], cards[index[5*i+3]], cards[index[5*i+4]]);
        if(max_score < score)
            max_score = score;
    }
    return max_score;
}

int cal_score(card_t *cards, int num_cards){
    int score;
    card_t hand;
    if(5 == num_cards){
        score = score5(cards[0], cards[1], cards[2], cards[3], cards[4]);
        hand = cards[0] | cards[1] | cards[2] | cards[3] | cards[4];
    }
    else if(6 == num_cards){
        score = score6(cards[0], cards[1], cards[2], cards[3], cards[4], cards[5]);
        hand = cards[0] | cards[1] | cards[2] | cards[3] | cards[4] | cards[5];
    }
    else if(7 == num_cards){
        score = score7(cards[0], cards[1], cards[2], cards[3], cards[4], cards[5], cards[6]);
        hand = cards[0] | cards[1] | cards[2] | cards[3] | cards[4] | cards[5] | cards[6];
    }
    else{
        return 0;
    }
    return score;
}


double prob_best(card_t* community,int num_community,card_t hole[2],int num_players){
    int num_deck, num_cards;
    int ret;
    int i,player;
    double best_score_count = 0;
    double p_best;
    int score;
    int op_score;
    int same_score_count;
    card_t taken=0;
    card_t *hand;
    card_t *deck;

    srand(time(NULL));
    hand = (card_t *)malloc((num_community+2)*sizeof(card_t));
    for(i=0; i< num_community; i++){
        hand[i] = community[i];
    }
    hand[num_community] = hole[0];
    hand[num_community+1] = hole[1];
    num_cards = num_community + 2;
    score = cal_score(hand, num_community+2);
    //printf("score %d",score);
    num_deck = TOTAL_DECK - num_cards;
    //printf("%d\n",num_community);
    for(i=0; i<num_community; i++){
        taken = taken | community[i];
        //printf("i %d ",i);
        //printf("%lx\n",taken);
    }
    taken = taken | hole[0];
    //printf("%lx\n",taken);
    taken = taken | hole[1];
    //printf("%lx\n",taken);
    deck = (card_t *)malloc(num_deck * sizeof(card_t));
    ret = init_deck(deck, taken);
    if (ret!= num_deck){
        printf(" ret number %d didn't equal num_deck %d.", ret, num_deck);
        abort();
    }
    best_score_count = 0;
    for(i=0; i<MAX_TEST; i++){
        shuffle(deck,num_deck);
        same_score_count = 1;
        for(player = 0; player<num_players-1;player++){
            hand[num_community] = deck[2*player];
            hand[num_community+1] = deck[2*player+1];
            op_score = cal_score(hand, num_cards);
            //printf("op score %d\n",op_score);
            if (op_score > score){
                goto end_test;
            }
            else if(op_score == score){
                same_score_count += 1;
            }
        }
        //no body has a larger score than me
        best_score_count += 1.0/same_score_count;
end_test:
        ;
    }
    p_best = best_score_count/MAX_TEST;
    //printf("best count %f\n", best_score_count);
    //free(hand);
    //free(deck);
    return p_best;
}

double prob_best_after_flop(card_t* community,int num_community,card_t hole[2],int num_players){
    int num_deck, num_cards;
    int ret;
    int i,player;
    double best_score_count = 0;
    double p_best;
    int score;
    int op_score;
    int same_score_count;
    card_t taken=0;
    card_t *hand;
    card_t *deck;

    srand(time(NULL));
    hand = (card_t *)malloc((num_community+4)*sizeof(card_t));
    for(i=0; i< num_community; i++){
        hand[i] = community[i];
    }
    num_cards = num_community + 2;
    num_deck = TOTAL_DECK - num_cards;
    for(i=0; i<num_community; i++){
        taken = taken | community[i];
    }
    taken = taken | hole[0];
    taken = taken | hole[1];
    deck = (card_t *)malloc(num_deck * sizeof(card_t));
    ret = init_deck(deck, taken);
    if (ret!= num_deck){
        printf(" ret number %d didn't equal num_deck %d.", ret, num_deck);
        abort();
    }
    best_score_count = 0;
    for(i=0; i<MAX_TEST; i++){
        shuffle(deck,num_deck);
        //turn and river
        hand[num_community] = deck[0];
        hand[num_community+1] = deck[1];
        //player hole
        hand[num_community+2] = hole[0];
        hand[num_community+3] = hole[1];
        score = cal_score(hand, num_cards+2);
        same_score_count = 1;
        for(player = 0; player<num_players-1;player++){
            //oponent's hand
            hand[num_community+2] = deck[2*player+2];
            hand[num_community+3] = deck[2*player+3];
            op_score = cal_score(hand, num_cards+2);
            if (op_score > score){
                goto end_test;
            }
            else if(op_score == score){
                same_score_count += 1;
            }
        }
        //no body has a larger score than me
        best_score_count += 1.0/same_score_count;
end_test:
        ;
    }
    p_best = best_score_count/MAX_TEST;
    //free(hand);
    //free(deck);
    return p_best;
}

double prob_best_after_turn(card_t* community,int num_community,card_t hole[2],int num_players){
    int num_deck, num_cards;
    int ret;
    int i,player;
    double best_score_count = 0;
    double p_best;
    int score;
    int op_score;
    int same_score_count;
    card_t taken=0;
    card_t *hand;
    card_t *deck;

    srand(time(NULL));
    hand = (card_t *)malloc((num_community+3)*sizeof(card_t));
    for(i=0; i< num_community; i++){
        hand[i] = community[i];
    }
    num_cards = num_community + 2;
    num_deck = TOTAL_DECK - num_cards;
    for(i=0; i<num_community; i++){
        taken = taken | community[i];
    }
    taken = taken | hole[0];
    taken = taken | hole[1];
    deck = (card_t *)malloc(num_deck * sizeof(card_t));
    ret = init_deck(deck, taken);
    if (ret!= num_deck){
        printf(" ret number %d didn't equal num_deck %d.", ret, num_deck);
        abort();
    }
    best_score_count = 0;
    for(i=0; i<MAX_TEST; i++){
        shuffle(deck,num_deck);
        //river
        hand[num_community] = deck[0];
        //player hole
        hand[num_community+1] = hole[0];
        hand[num_community+2] = hole[1];
        score = cal_score(hand, num_cards+1);
        same_score_count = 1;
        for(player = 0; player<num_players-1;player++){
            //oponent's hand
            hand[num_community+1] = deck[2*player+1];
            hand[num_community+2] = deck[2*player+2];
            op_score = cal_score(hand, num_cards+1);
            if (op_score > score){
                goto end_test;
            }
            else if(op_score == score){
                same_score_count += 1;
            }
        }
        //no body has a larger score than me
        best_score_count += 1.0/same_score_count;
end_test:
        ;
    }
    p_best = best_score_count/MAX_TEST;
    //free(hand);
    //free(deck);
    return p_best;
}



int score5(card_t c1, card_t c2, card_t c3, card_t c4, card_t c5) {
    int ones = 0, twos = 0, threes = 0, fours = 0;
    int s;

    card_t hand = c1 | c2 | c3 | c4 | c5;

    // build rankmask for each suit
    int hearts = hand & 8191;
    int clubs = (hand >> 13) & 8191;
    int diamonds = (hand >> 26) & 8191;
    int spades = hand >> 39;
    int rankmask = hearts | clubs | diamonds | spades;

    // count the number of cards of each suit
    int nhearts = nbits[hearts];
    int nspades = nbits[spades];
    int nclubs = nbits[clubs];
    int ndiamonds = nbits[diamonds];

    // if a hand has a flush, the best hand is a flush or straight flush
    // lookup the result
    if (nhearts >= 5)
        return flush[hearts];
    else if (nspades >= 5)
        return flush[spades];
    else if (nclubs >= 5)
        return flush[clubs];
    else if (ndiamonds >= 5)
        return flush[diamonds];

    if (nbits[rankmask] == 5)
        return unique[rankmask];

    fours = (hearts & clubs & diamonds & spades);
    threes = (( clubs & diamonds )|( hearts & spades )) & (( clubs & hearts )|( diamonds & spades ));
    twos = rankmask ^ (hearts ^ clubs ^ diamonds ^ spades);
    ones = rankmask & (~(twos | threes | fours));

    if (fours)
        return QUAD | fours << 13 | ones;

    if ((threes > 0) & (twos > 0))
        return FULLHOUSE | threes << 13 | twos;

    s = straight[rankmask];
    if (s)
        return STRAIGHT | s;

    if (threes) {
        return TRIP | threes << 13 | ones;
    }

    if (nbits[twos] == 2)
        return TWOPAIR | twos << 13 | ones;

    if (twos)
        return PAIR | twos << 13 | ones;

    return ones;

}

int score7(card_t c1, card_t c2, card_t c3, card_t c4, card_t c5, card_t c6, card_t c7) {
    // each card is a bitmask
    int ones = 0, twos = 0, threes = 0, fours = 0, notfours = 0;
    int s;

    card_t hand = c1 | c2 | c3 | c4 | c5 | c6 | c7;
    int hearts = hand & 8191;
    int clubs = (hand >> 13) & 8191;
    int diamonds = (hand >> 26) & 8191;
    int spades = hand >> 39;
    int rankmask = hearts | clubs | diamonds | spades;

    // count the number of cards of each suit
    int nhearts = nbits[hearts];
    int nspades = nbits[spades];
    int nclubs = nbits[clubs];
    int ndiamonds = nbits[diamonds];

    // if a hand has a flush, the best hand is a flush or straight flush
    // lookup the result
    if (nhearts >= 5)
        return flush[hearts];
    else if (nspades >= 5)
        return flush[spades];
    else if (nclubs >= 5)
        return flush[clubs];
    else if (ndiamonds >= 5)
        return flush[diamonds];

    // lookup result for 7 unique cards
    if (nbits[rankmask] == 7)
        return unique[rankmask];

    // 13-bit mask of which ranks have 4 cards
    fours = (hearts & clubs & diamonds & spades);
    notfours = rankmask & (~fours);
    if (fours) {
        return (QUAD) | (fours << 13) | high1[notfours];
    }

    // 13-bit mask of which ranks have 3/2 cards
    // technically quads are also in these masks, but we
    // determined above there are no quads.
    threes = (( clubs & diamonds )|( hearts & spades )) & (( clubs & hearts )|( diamonds & spades ));
    twos = rankmask ^ (hearts ^ clubs ^ diamonds ^ spades);

    // Full house
    if ((threes != 0) & (twos != 0))
        return (FULLHOUSE) | (threes << 13) | high1[twos];

    if (nbits[threes] == 2)
        return (FULLHOUSE) | (high1[threes] << 13) | low[threes];

    s = straight[rankmask];
    if (s)
        return STRAIGHT | s;

    // 13-bit mask for which ranks appear once
    ones = rankmask & (~(twos | threes | fours));

    if (threes)
        return TRIP | threes << 13 | high2[ones];

    if (nbits[twos] == 3)
        return TWOPAIR | (high2[twos] << 13) | high1[low[twos] | ones];

    if (nbits[twos] == 2)
        return TWOPAIR | twos << 13 | high1[ones];

    if (twos)
        return PAIR | twos << 13 | high3[ones];

    return high5[ones];
}

void deck(card_t *deck) {
    int i;
    for(i=0; i < 52; i++) {
        deck[i] = 1L << i;
    }
}

void all7() {
    int i, j, k, l, m, n, o;
    int score=0;
    int sums[] = {0, 0, 0, 0, 0, 0, 0, 0, 0};
    card_t d[52];
    deck(d);

    for(i=0; i<9; i++) {
        sums[i] = 0;
    }

    for(i=0; i<52; i++) {
        for(j=i+1; j<52; j++) {
            for(k=j+1; k<52; k++) {
                for(l=k+1; l<52; l++) {
                    for(m=l+1; m<52; m++) {
                        for(n=m+1; n<52; n++) {
                            for(o=n+1; o<52; o++) {
                                score = score7(d[i], d[j], d[k], d[l], d[m], d[n], d[o]);
                                sums[score >> 26] += 1;
                            }
                        }
                    }
                }
            }
        }
    }

    for(i=0; i<9; i++) {
        printf("%20.20s %i\n", HAND_NAMES[i], sums[i]);
    }

}


int main(){
    int score;
    card_t * deck;
    srand(time(NULL));
    card_t community[] = {1L<<32, 1L<<33, 1L<<34, 1L<<13, 1L<<40};
    card_t hole[] = {1L<<10, 1L<<39};
    double p_win;
    
    p_win = prob_best_after_flop(community,3,hole,2);
    printf("ppob best after flop win %lf\n",p_win);
    p_win = prob_best_after_turn(community,4,hole,2);
    printf("ppob best after turn win %lf\n",p_win);
    p_win = prob_best(community,5,hole,2);
    printf("prob best pwin %lf\n",p_win);
    //score = score5(1L<<27,1L<<28,1L<<29,1L<<30,2L<<31);
    /*
    deck = (card_t *)malloc(52*sizeof(card_t));
    init_deck(deck,0L);
    for(int i=0;i<52;i++)
        printf("%ld ",deck[i]);
    printf("====\n");
    shuffle(deck,52);
    for(int i=0;i<52;i++)
        printf("%ld ",deck[i]);
        */
}
