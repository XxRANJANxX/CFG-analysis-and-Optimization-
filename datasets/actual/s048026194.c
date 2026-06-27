A[20000];z(int*a,int*b){return*b-*a;}
main(n,i,j){for(;scanf("%d",&n),n;puts(i>n?"No":"Yes")){
for(i=0;i<n*2;i++)scanf("%d",A+i);
for(i=qsort(A,n,4,z);i<n;i=A[i]?n+1:i+1)for(j=0;j<n;j++)if(A[j+n])A[i]--,A[j+n]--;
}exit(0);}