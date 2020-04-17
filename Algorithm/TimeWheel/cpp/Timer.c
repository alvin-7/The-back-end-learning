#include <stddef.h>
#include <stdlib.h>
#include <sys/time.h>
#include "Timer.h"

// 获取基准时间
static uint32 GetJiffies_old(void)
{
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec * 1000 + tv.tv_usec / 1000;
}

static uint32 GetJiffies(void)
{
    struct timespec ts;  // 精确到纳秒（10 的 -9 次方秒）
    // 使用 clock_gettime 函数时，有些系统需连接 rt 库，加 -lrt 参数，有些不需要连接 rt 库
    clock_gettime(CLOCK_MONOTONIC, &ts);  // 获取时间。其中，CLOCK_MONOTONIC 表示从系统启动这一刻起开始计时,不受系统时间被用户改变的影响
    return (ts.tv_sec * 1000 + ts.tv_nsec / 1000000);  // 返回毫秒时间
}

// 将双向循环链表的新结点插入到结点 pPrev 和 pNext 之间
static void ListTimerInsert(struct LIST_TIMER *pNew, struct LIST_TIMER *pPrev, struct LIST_TIMER *pNext)
{
    pNext->pPrev = pNew;
    pNew->pNext = pNext;
    pNew->pPrev = pPrev;
    pPrev->pNext = pNew;
}

static void ListTimerInsertHead(struct LIST_TIMER *pNew, struct LIST_TIMER *pHead)
{
    ListTimerInsert(pNew, pHead, pHead->pNext);
}

static void ListTimerInsertTail(struct LIST_TIMER *pNew, struct LIST_TIMER *pHead)
{
    ListTimerInsert(pNew, pHead->pPrev, pHead);
}

// 使用新结点 pNew 替换 pOld 在双向循环链表中的位置。如果双向链表中仅有一个结点 pOld，使用 pNew 替换后，同样，仅有一个结点 pNew
static void ListTimerReplace(struct LIST_TIMER *pOld, struct LIST_TIMER *pNew)
{
    pNew->pNext = pOld->pNext;
    pNew->pNext->pPrev = pNew;
    pNew->pPrev = pOld->pPrev;
    pNew->pPrev->pNext = pNew;
}

// 使用新结点 pNew 替换 pOld 在双向循环链表中的位置。
static void ListTimerReplaceInit(struct LIST_TIMER *pOld, struct LIST_TIMER *pNew)
{
    ListTimerReplace(pOld, pNew);
    // 使用 pNew 替换 pOld 在双向循环链表中的位置后，pOld 结点从链表中独立出来了，所以要让 pOld 指向自己
    pOld->pNext = pOld;
    pOld->pPrev = pOld;
}

// 初始化时间轮中的所有 tick。初始化后，每个 tick 中的双向链表只有一个头结点
static void InitArrayListTimer(struct LIST_TIMER *arrListTimer, uint32 nSize)
{
    uint32 i;
    for(i=0; i<nSize; i++)
    {
        arrListTimer[i].pPrev = &arrListTimer[i];
        arrListTimer[i].pNext = &arrListTimer[i];
    }
}

static void DeleteArrayListTimer(struct LIST_TIMER *arrListTimer, uint32 uSize)
{
    struct LIST_TIMER listTmr, *pListTimer;
    struct TIMER_NODE *pTmr;
    uint32 idx;

    for(idx=0; idx<uSize; idx++)
    {
        ListTimerReplaceInit(&arrListTimer[idx], &listTmr);
        pListTimer = listTmr.pNext;
        while(pListTimer != &listTmr)
        {
            pTmr = (struct TIMER_NODE *)((uint8 *)pListTimer - offsetof(struct TIMER_NODE, ltTimer));
            pListTimer = pListTimer->pNext;
            free(pTmr);
        }
    }
}

// 根据计时器的结束时间计算所属时间轮、在该时间轮上的 tick、然后将新计时器结点插入到该 tick 的双向循环链表的尾部
static void AddTimer(LPTIMERMANAGER lpTimerManager, LPTIMERNODE pTmr)
{
    struct LIST_TIMER *pHead;
    uint32 i, uDueTime, uExpires;

    uExpires = pTmr->uExpires; // 定时器到期的时刻
    uDueTime = uExpires - lpTimerManager->uJiffies;
    if (uDueTime < TVR_SIZE)   // idx < 256 (2的8次方)
    {
        i = uExpires & TVR_MASK; // expires & 255
        pHead = &lpTimerManager->arrListTimer1[i];
    }
    else if (uDueTime < 1 << (TVR_BITS + TVN_BITS)) // idx < 16384 (2的14次方)
    {
        i = (uExpires >> TVR_BITS) & TVN_MASK;      // i = (expires>>8) & 63
        pHead = &lpTimerManager->arrListTimer2[i];
    }
    else if (uDueTime < 1 << (TVR_BITS + 2 * TVN_BITS)) // idx < 1048576 (2的20次方)
    {
        i = (uExpires >> (TVR_BITS + TVN_BITS)) & TVN_MASK; // i = (expires>>14) & 63
        pHead = &lpTimerManager->arrListTimer3[i];
    }
    else if (uDueTime < 1 << (TVR_BITS + 3 * TVN_BITS)) // idx < 67108864 (2的26次方)
    {
        i = (uExpires >> (TVR_BITS + 2 * TVN_BITS)) & TVN_MASK; // i = (expires>>20) & 63
        pHead = &lpTimerManager->arrListTimer4[i];
    }
    else if ((signed long) uDueTime < 0)
    {
        /*
         * Can happen if you add a timer with expires == jiffies,
         * or you set a timer to go off in the past
         */
        pHead = &lpTimerManager->arrListTimer1[(lpTimerManager->uJiffies & TVR_MASK)];
    }
    else
    {
        /* If the timeout is larger than 0xffffffff on 64-bit
         * architectures then we use the maximum timeout:
         */
        if (uDueTime > 0xffffffffUL)
        {
            uDueTime = 0xffffffffUL;
            uExpires = uDueTime + lpTimerManager->uJiffies;
        }
        i = (uExpires >> (TVR_BITS + 3 * TVN_BITS)) & TVN_MASK; // i = (expires>>26) & 63
        pHead = &lpTimerManager->arrListTimer5[i];
    }
    ListTimerInsertTail(&pTmr->ltTimer, pHead);
}

// 遍历时间轮 arrlistTimer 的双向循环链表，将其中的计时器根据到期时间加入到指定的时间轮中
static uint32 CascadeTimer(LPTIMERMANAGER lpTimerManager, struct LIST_TIMER *arrListTimer, uint32 idx)
{
    struct LIST_TIMER listTmr, *pListTimer;
    struct TIMER_NODE *pTmr;

    ListTimerReplaceInit(&arrListTimer[idx], &listTmr);
    pListTimer = listTmr.pNext;
    // 遍历双向循环链表，添加定时器
    while(pListTimer != &listTmr)
    {
        // 根据结构体 struct TIMER_NODE 的成员 ltTimer 的指针地址和该成员在结构体中的便宜量，计算结构体 struct TIMER_NODE 的地址
        pTmr = (struct TIMER_NODE *)((uint8 *)pListTimer - offsetof(struct TIMER_NODE, ltTimer));
        pListTimer = pListTimer->pNext;
        AddTimer(lpTimerManager, pTmr);
    }
    return idx;
}

static void RunTimer(LPTIMERMANAGER lpTimerManager)
{
#define INDEX(N) ((lpTimerManager->uJiffies >> (TVR_BITS + (N) * TVN_BITS)) & TVN_MASK)
    uint32 idx, uJiffies;
    struct LIST_TIMER listTmrExpire, *pListTmrExpire;
    struct TIMER_NODE *pTmr;

    if(NULL == lpTimerManager)
        return;
    uJiffies = GetJiffies();
    pthread_mutex_lock(&lpTimerManager->lock);
    while(TIME_AFTER_EQ(uJiffies, lpTimerManager->uJiffies))
    {
        // unint32 共 32bit，idx 为当前时间的低 8bit，INDEX(0) 为次 6bit，INDEX(1) 为再次 6bit，INDEX(2) 为再次 6bit，INDEX(3) 为高 6bit
        // 如果 1 级时间轮的 256 毫秒走完了，会遍历把 2 级时间轮中的计时器，将其中的计时器根据到期时间加入到指定时间轮。这样 1 级时间轮中就有计时器了。
        //  如果 1、2 级时间轮的 256*64 毫秒都走完了，会遍历 3 级时间轮，将其中的计时器加入到指定时间轮。这样 1 级和 2 级时间轮中就有计时器了。
        //   如果 1、2、3 级时间轮的 256*64*64 毫秒都走完了，...
        //    如果 1、2、3、4 级时间轮的 256*64*64*64 毫秒都走完了，...
        idx = lpTimerManager->uJiffies & TVR_MASK;
        if (!idx &&
                (!CascadeTimer(lpTimerManager, lpTimerManager->arrListTimer2, INDEX(0))) &&
                (!CascadeTimer(lpTimerManager, lpTimerManager->arrListTimer3, INDEX(1))) &&
                !CascadeTimer(lpTimerManager, lpTimerManager->arrListTimer4, INDEX(2)))
            CascadeTimer(lpTimerManager, lpTimerManager->arrListTimer5, INDEX(3));
        pListTmrExpire = &listTmrExpire;
        // 新结点 pListTmrExpire 替换 arrListTimer1[idx] 后，双向循环链表 arrListTimer1[idx] 就只有它自己一个结点了。pListTmrExpire 成为双向循环链表的入口
        ListTimerReplaceInit(&lpTimerManager->arrListTimer1[idx], pListTmrExpire);
        // 遍历时间轮 arrListTimer1 的双向循环链表，执行该链表所有定时器的回调函数
        pListTmrExpire = pListTmrExpire->pNext;
        while(pListTmrExpire != &listTmrExpire)
        {
            pTmr = (struct TIMER_NODE *)((uint8 *)pListTmrExpire - offsetof(struct TIMER_NODE, ltTimer));
            pListTmrExpire = pListTmrExpire->pNext;
            pTmr->timerFn(pTmr->pParam);
            //
            if(pTmr->uPeriod != 0)
            {
                pTmr->uExpires = lpTimerManager->uJiffies + pTmr->uPeriod;
                AddTimer(lpTimerManager, pTmr);
            }
            else free(pTmr);
        }
        lpTimerManager->uJiffies++;
    }
    pthread_mutex_unlock(&lpTimerManager->lock);
}

// 计时器线程。以 1 毫秒为单位进行计时
static void *ThreadRunTimer(void *pParam)
{
    LPTIMERMANAGER pTimerMgr;

    pTimerMgr = (LPTIMERMANAGER)pParam;
    if(pTimerMgr == NULL)
        return NULL;
    while(!pTimerMgr->uExitFlag)
    {
        RunTimer(pTimerMgr);
        SleepMilliseconds(1);  // 线程睡 1 毫秒
    }
    return NULL;
}

// 睡 uMs 毫秒
void SleepMilliseconds(uint32 uMs)
{
    struct timeval tv;
    tv.tv_sec = 0;
    tv.tv_usec = uMs * 1000;  // tv.tv_usec 单位是微秒
    select(0, NULL, NULL, NULL, &tv);
}

// 创建定时器管理器
LPTIMERMANAGER CreateTimerManager(void)
{
    LPTIMERMANAGER lpTimerMgr = (LPTIMERMANAGER)malloc(sizeof(TIMERMANAGER));
    if(lpTimerMgr != NULL)
    {
        lpTimerMgr->thread = (pthread_t)0;
        lpTimerMgr->uExitFlag = 0;
        pthread_mutex_init(&lpTimerMgr->lock, NULL);
        lpTimerMgr->uJiffies = GetJiffies();
        InitArrayListTimer(lpTimerMgr->arrListTimer1, sizeof(lpTimerMgr->arrListTimer1)/sizeof(lpTimerMgr->arrListTimer1[0]));
        InitArrayListTimer(lpTimerMgr->arrListTimer2, sizeof(lpTimerMgr->arrListTimer2)/sizeof(lpTimerMgr->arrListTimer2[0]));
        InitArrayListTimer(lpTimerMgr->arrListTimer3, sizeof(lpTimerMgr->arrListTimer3)/sizeof(lpTimerMgr->arrListTimer3[0]));
        InitArrayListTimer(lpTimerMgr->arrListTimer4, sizeof(lpTimerMgr->arrListTimer4)/sizeof(lpTimerMgr->arrListTimer4[0]));
        InitArrayListTimer(lpTimerMgr->arrListTimer5, sizeof(lpTimerMgr->arrListTimer5)/sizeof(lpTimerMgr->arrListTimer5[0]));
        lpTimerMgr->thread = ThreadCreate(ThreadRunTimer, lpTimerMgr);
    }
    return lpTimerMgr;
}

// 删除定时器管理器
void DestroyTimerManager(LPTIMERMANAGER lpTimerManager)
{
    if(NULL == lpTimerManager)
        return;
    lpTimerManager->uExitFlag = 1;
    if((pthread_t)0 != lpTimerManager->thread)
    {
        ThreadJoin(lpTimerManager->thread);
        ThreadDestroy(lpTimerManager->thread);
        lpTimerManager->thread = (pthread_t)0;
    }
    DeleteArrayListTimer(lpTimerManager->arrListTimer1, sizeof(lpTimerManager->arrListTimer1)/sizeof(lpTimerManager->arrListTimer1[0]));
    DeleteArrayListTimer(lpTimerManager->arrListTimer2, sizeof(lpTimerManager->arrListTimer2)/sizeof(lpTimerManager->arrListTimer2[0]));
    DeleteArrayListTimer(lpTimerManager->arrListTimer3, sizeof(lpTimerManager->arrListTimer3)/sizeof(lpTimerManager->arrListTimer3[0]));
    DeleteArrayListTimer(lpTimerManager->arrListTimer4, sizeof(lpTimerManager->arrListTimer4)/sizeof(lpTimerManager->arrListTimer4[0]));
    DeleteArrayListTimer(lpTimerManager->arrListTimer5, sizeof(lpTimerManager->arrListTimer5)/sizeof(lpTimerManager->arrListTimer5[0]));
    pthread_mutex_destroy(&lpTimerManager->lock);
    free(lpTimerManager);
}

// 创建一个定时器。fnTimer 回调函数地址。pParam 回调函数的参数。uDueTime 首次触发的超时时间间隔。uPeriod 定时器循环周期，若为0，则该定时器只运行一次。
LPTIMERNODE CreateTimer(LPTIMERMANAGER lpTimerManager, void (*timerFn)(void*), void *pParam, uint32 uDueTime, uint32 uPeriod)
{
    LPTIMERNODE pTmr = NULL;
    if(NULL == timerFn || NULL == lpTimerManager)
        return NULL;
    pTmr = (LPTIMERNODE)malloc(sizeof(TIMERNODE));
    if(pTmr != NULL)
    {
        pTmr->uPeriod = uPeriod;
        pTmr->timerFn = timerFn;
        pTmr->pParam = pParam;

        pthread_mutex_lock(&lpTimerManager->lock);
        pTmr->uExpires = lpTimerManager->uJiffies + uDueTime;
        AddTimer(lpTimerManager, pTmr);
        pthread_mutex_unlock(&lpTimerManager->lock);
    }
    return pTmr;
}

//删除定时器
int32 DeleteTimer(LPTIMERMANAGER lpTimerManager, LPTIMERNODE lpTimer)
{
    struct LIST_TIMER *pListTmr;
    if(NULL != lpTimerManager && NULL != lpTimer)
    {
        pthread_mutex_lock(&lpTimerManager->lock);
        pListTmr = &lpTimer->ltTimer;
        pListTmr->pPrev->pNext = pListTmr->pNext;
        pListTmr->pNext->pPrev = pListTmr->pPrev;
        free(lpTimer);
        pthread_mutex_unlock(&lpTimerManager->lock);
        return 0;
    }
    else
        return -1;
}