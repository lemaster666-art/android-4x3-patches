/* Authored JNI/Mono embedding bridge. No original native library is patched.
 * JNI table indices are fixed by the JNI 1.6 ABI. Only required operations are declared.
 * No application-protection checks are disabled. */
typedef unsigned char jboolean;
typedef int jint;
typedef void *jobject;
typedef void *jclass;
typedef void *jmethodID;
typedef void JNIEnv;
typedef void JavaVM;
extern void *dlsym(void *, const char *);
extern void *dlopen(const char *,int);
#define EXPORT __attribute__((visibility("default")))
#define FN(env,index,type) ((type)((*(void ***)env)[index]))
static JavaVM *vm;
static jclass bridge;
static jmethodID ready_id,finish_id,fail_id,note_id;
static JNIEnv *environment(void) {
    JNIEnv *env=0;
    if(!vm || FN(vm,6,jint(*)(JavaVM*,void**,jint))(vm,(void**)&env,0x10006)!=0)return 0;
    return env;
}
static int exception(JNIEnv *env) {
    if(FN(env,228,jboolean(*)(JNIEnv*))(env)) {
        FN(env,17,void(*)(JNIEnv*))(env);return 1;
    }return 0;
}
static void note(JNIEnv *env,const char *text) {
    if(!bridge || !note_id)return;
    jobject s=FN(env,167,jobject(*)(JNIEnv*,const char*))(env,text);
    if(!s || exception(env))return;
    FN(env,141,void(*)(JNIEnv*,jclass,jmethodID,...))(env,bridge,note_id,s);
    FN(env,23,void(*)(JNIEnv*,jobject))(env,s);exception(env);
}
EXPORT jint JNI_OnLoad(JavaVM *input,void *reserved){(void)reserved;vm=input;return 0x10006;}
EXPORT jint marvel_ready(jobject activity) {
    JNIEnv *env=environment();if(!env || !bridge || !ready_id)return 0;
    jboolean result=FN(env,117,jboolean(*)(JNIEnv*,jclass,jmethodID,...))(env,bridge,ready_id,activity);
    return exception(env)?0:result;
}
EXPORT jint marvel_finish(jobject activity) {
    JNIEnv *env=environment();if(!env || !bridge || !finish_id)return 0;
    FN(env,141,void(*)(JNIEnv*,jclass,jmethodID,...))(env,bridge,finish_id,activity);
    return exception(env)?0:1;
}
EXPORT jint marvel_fail_open(jobject activity) {
    JNIEnv *env=environment();if(!env || !bridge || !fail_id)return 0;
    FN(env,141,void(*)(JNIEnv*,jclass,jmethodID,...))(env,bridge,fail_id,activity);
    return exception(env)?0:1;
}
EXPORT jboolean Java_com_vocies61_marvelcosmic_EnhancedBridge_nativeStart(JNIEnv *env,jclass cls,jobject activity,jobject bytes) {
    if(!bridge) {
        bridge=FN(env,21,jobject(*)(JNIEnv*,jobject))(env,cls);
        ready_id=FN(env,113,jmethodID(*)(JNIEnv*,jclass,const char*,const char*))(env,cls,"onReady","(Landroid/app/Activity;)Z");
        finish_id=FN(env,113,jmethodID(*)(JNIEnv*,jclass,const char*,const char*))(env,cls,"onFinished","(Landroid/app/Activity;)V");
        fail_id=FN(env,113,jmethodID(*)(JNIEnv*,jclass,const char*,const char*))(env,cls,"onFailure","(Landroid/app/Activity;)V");
        note_id=FN(env,113,jmethodID(*)(JNIEnv*,jclass,const char*,const char*))(env,cls,"note","(Ljava/lang/String;)V");
    }
    if(exception(env) || !bridge || !ready_id || !finish_id || !fail_id || !note_id)return 0;
    jint length=FN(env,171,jint(*)(JNIEnv*,jobject))(env,bytes);
    if(length<1024 || length>2*1024*1024)return 0;
    void *mono_library=dlopen("libmonosgen-2.0.so",6); /* RTLD_NOW | RTLD_NOLOAD */
    if(!mono_library){note(env,"Initialized Mono runtime was not found");return 0;}
    void *(*get_root)(void)=dlsym(mono_library,"mono_get_root_domain");
    void *(*attach)(void*)=dlsym(mono_library,"mono_thread_attach");
    void *(*open_image)(char*,unsigned int,int,int*,int,const char*)=dlsym(mono_library,"mono_image_open_from_data_with_name");
    void *(*load_assembly)(void*,const char*,int*,int)=dlsym(mono_library,"mono_assembly_load_from_full");
    void *(*find_class)(void*,const char*,const char*)=dlsym(mono_library,"mono_class_from_name");
    void *(*find_method)(void*,const char*,int)=dlsym(mono_library,"mono_class_get_method_from_name");
    void *(*invoke)(void*,void*,void**,void**)=dlsym(mono_library,"mono_runtime_invoke");
    if(!get_root || !attach || !open_image || !load_assembly || !find_class || !find_method || !invoke){note(env,"Required Mono embedding API unavailable");return 0;}
    void *domain=get_root();if(!domain || !attach(domain))return 0;
    char *data=FN(env,184,char*(*)(JNIEnv*,jobject,jboolean*))(env,bytes,0);
    if(!data || exception(env))return 0;
    int status=0;
    void *image=open_image(data,(unsigned)length,1,&status,0,"Android4x3.Marvel.Enhancements.dll");
    FN(env,192,void(*)(JNIEnv*,jobject,char*,jint))(env,bytes,data,2);
    if(!image || status!=0){note(env,"Authored managed helper image could not be opened");return 0;}
    void *assembly=load_assembly(image,"Android4x3.Marvel.Enhancements.dll",&status,0);
    if(!assembly || status!=0){note(env,"Authored managed helper assembly could not be loaded");return 0;}
    void *klass=find_class(image,"Android4x3.Marvel","Enhancements");
    void *method=klass?find_method(klass,"Start",1):0;
    if(!method){note(env,"Authored managed helper entry point missing");return 0;}
    jobject owned=FN(env,21,jobject(*)(JNIEnv*,jobject))(env,activity);
    if(!owned || exception(env))return 0;
    void *argument=owned;void *args[1]={&argument};void *error=0;
    invoke(method,0,args,&error);
    FN(env,22,void(*)(JNIEnv*,jobject))(env,owned);
    if(error){note(env,"Managed helper rejected startup before launching its worker");return 0;}
    note(env,"Authored startup/exit helper dispatched");return 1;
}
