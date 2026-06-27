#include <stdio.h>
#include <stdlib.h>
int c(const void *v1,const void *v2){
    return *(int *)v1-*(int *)v2;
}
int main(void){
    int num,i,o,t,line[50],line1[25],sum=0,sign;
    for(;sign=0,scanf("%d",&num),num;){
        for(i=0,t=0;i<num*2;i++){
            scanf("%d",&line[i]);
            if(i%2)
                line1[t++]=line[i];
        }
        qsort(line1,t,4,c);
        for(sum=0,i=0;i<num;i++){
            for(o=1;o<num*2;o+=2){
                if(line1[i]==line[o]){
                    sum+=line[o-1];
                    break;
                }
            }
            if(line1[i]<sum){
                sign=1;
                break;
            }
        }
        printf("%s\n",sign==1?"No":"Yes");
    }
    return 0;
}