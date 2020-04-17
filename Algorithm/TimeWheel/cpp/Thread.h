#ifndef _THREAD_H_
#define _THREAD_H_

#include <pthread.h>
#include "def.h"

typedef void* (*FNTHREAD)(void *pParam);

pthread_t ThreadCreate(FNTHREAD fnThreadProc, void *pParam);
void ThreadJoin(pthread_t thread);
void ThreadDestroy(pthread_t thread);

#endif //_THREAD_H_