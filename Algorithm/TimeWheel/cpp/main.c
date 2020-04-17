#include <stdio.h>
#include "Timer.h"

void TimerFun(void *pParam)
{
    LPTIMERMANAGER pMgr;
    pMgr = (LPTIMERMANAGER)pParam;
    printf("Timer expire! Jiffies: %lu\n", pMgr->uJiffies);
}

int main(void)
{
    LPTIMERMANAGER pMgr;
    LPTIMERNODE pTn;
    pMgr = CreateTimerManager();
    CreateTimer(pMgr, TimerFun, pMgr, 2000, 0);
    pTn = CreateTimer(pMgr, TimerFun, pMgr, 4000, 1000);
    SleepMilliseconds(10001);
    DeleteTimer(pMgr, pTn);
    SleepMilliseconds(3000);
    DestroyTimerManager(pMgr);
    return 0;
}