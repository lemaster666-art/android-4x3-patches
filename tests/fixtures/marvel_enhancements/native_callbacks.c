/* Authored host-test callbacks; not the APK's JNI loader. */
static int ready,finish,failure,result=1;
int marvel_ready(void *activity){(void)activity;ready++;return result;}
int marvel_finish(void *activity){(void)activity;finish++;return 1;}
int marvel_fail_open(void *activity){(void)activity;failure++;return 1;}
int ReadyCount(void){return ready;}
int FinishCount(void){return finish;}
int FailureCount(void){return failure;}
void SetReadyResult(int value){result=value;}
