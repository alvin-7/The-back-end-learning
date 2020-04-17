#include "Thread.h"

pthread_t ThreadCreate(FNTHREAD fnThreadProc, void *pParam)
{
    pthread_t t;
    if(fnThreadProc == NULL)
        return 0;
    if(pthread_create(&t, NULL, fnThreadProc, pParam) == 0)
        return t;
    else
        return (pthread_t)0;
}

void ThreadJoin(pthread_t thread)
{
    pthread_join(thread, NULL);
}

void ThreadDestroy(pthread_t thread)
{
}