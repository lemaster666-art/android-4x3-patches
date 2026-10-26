/* Authored JNI/Mono embedding test doubles. No Android/game code is executed. */
#include <jni.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
extern jint JNI_OnLoad(JavaVM*,void*);
extern jboolean Java_com_vocies61_marvelcosmic_EnhancedBridge_nativeStart(JNIEnv*,jclass,jobject,jbyteArray);
extern int marvel_ready(jobject);
extern int marvel_finish(jobject);
extern int marvel_fail_open(jobject);
static JNIEnv environment;
static int invokes,ready,finished,failed,released,cleared;
static const char *mode;
static jobject expected_activity=(jobject)123;
static unsigned char bytes[2048];
static jboolean JNICALL check(JNIEnv *env){(void)env;return 0;}
static void JNICALL clear(JNIEnv *env){(void)env;cleared++;}
static jobject JNICALL global(JNIEnv *env,jobject value){(void)env;return value;}
static void JNICALL drop(JNIEnv *env,jobject value){(void)env;(void)value;}
static jstring JNICALL string(JNIEnv *env,const char *value){(void)env;return (jstring)value;}
static jsize JNICALL length(JNIEnv *env,jarray array){(void)env;(void)array;return !strcmp(mode,"oversize")?3000000:2048;}
static jbyte * JNICALL elements(JNIEnv *env,jbyteArray array,jboolean *copy){(void)env;(void)array;(void)copy;return (jbyte*)bytes;}
static void JNICALL release(JNIEnv *env,jbyteArray array,jbyte *data,jint disposition){(void)env;(void)array;if(data!=(jbyte*)bytes || disposition!=JNI_ABORT)exit(20);released++;}
static jmethodID JNICALL method(JNIEnv *env,jclass cls,const char *name,const char *sig){
 (void)env;(void)cls;
 if(!strcmp(name,"onReady") && !strcmp(sig,"(Landroid/app/Activity;)Z"))return (jmethodID)1;
 if(!strcmp(name,"onFinished") && !strcmp(sig,"(Landroid/app/Activity;)V"))return (jmethodID)2;
 if(!strcmp(name,"onFailure") && !strcmp(sig,"(Landroid/app/Activity;)V"))return (jmethodID)3;
 if(!strcmp(name,"note") && !strcmp(sig,"(Ljava/lang/String;)V"))return (jmethodID)4;
 exit(21);
}
static jboolean JNICALL boolean_call(JNIEnv *env,jclass cls,jmethodID id,...){
 (void)env;(void)cls;va_list args;va_start(args,id);jobject activity=va_arg(args,jobject);va_end(args);
 if(id!=(jmethodID)1 || activity!=expected_activity)exit(22);ready++;return 1;
}
static void JNICALL void_call(JNIEnv *env,jclass cls,jmethodID id,...){
 (void)env;(void)cls;va_list args;va_start(args,id);jobject value=va_arg(args,jobject);va_end(args);
 if(id==(jmethodID)4)return;
 if(value!=expected_activity)exit(23);
 if(id==(jmethodID)2)finished++;else if(id==(jmethodID)3)failed++;else exit(24);
}
static jint JNICALL get_environment(JavaVM *vm,void **out,jint version){(void)vm;if(version!=JNI_VERSION_1_6)exit(25);*out=&environment;return JNI_OK;}
static void *root(void){return (void*)10;}
static void *attach(void *domain){if(domain!=(void*)10)exit(26);return (void*)11;}
static void *image(char *data,unsigned size,int copy,int *status,int reflection_only,const char *name){
 if(data!=(char*)bytes || size!=2048 || copy!=1 || reflection_only!=0 || strcmp(name,"Android4x3.Marvel.Enhancements.dll"))exit(27);
 *status=0;return (void*)12;
}
static void *assembly(void *data,const char *name,int *status,int reflection_only){if(data!=(void*)12 || reflection_only || strcmp(name,"Android4x3.Marvel.Enhancements.dll"))exit(28);*status=0;return (void*)13;}
static void *klass(void *data,const char *ns,const char *name){if(data!=(void*)12 || strcmp(ns,"Android4x3.Marvel") || strcmp(name,"Enhancements"))exit(29);return (void*)14;}
static void *entry(void *type,const char *name,int count){if(type!=(void*)14 || strcmp(name,"Start") || count!=1)exit(30);return (void*)15;}
static void *invoke(void *target,void *instance,void **args,void **error){
 if(target!=(void*)15 || instance || *(jobject*)args[0]!=expected_activity)exit(31);
 invokes++;*error=!strcmp(mode,"managed-error")?(void*)99:0;return 0;
}
void *dlopen(const char *name,int flags){if(strcmp(name,"libmonosgen-2.0.so") || flags!=6)exit(32);return (void*)16;}
void *dlsym(void *library,const char *name){
 if(library!=(void*)16)exit(33);
 if(!strcmp(mode,"missing-api"))return 0;
 if(!strcmp(name,"mono_get_root_domain"))return (void*)root;
 if(!strcmp(name,"mono_thread_attach"))return (void*)attach;
 if(!strcmp(name,"mono_image_open_from_data_with_name"))return (void*)image;
 if(!strcmp(name,"mono_assembly_load_from_full"))return (void*)assembly;
 if(!strcmp(name,"mono_class_from_name"))return (void*)klass;
 if(!strcmp(name,"mono_class_get_method_from_name"))return (void*)entry;
 if(!strcmp(name,"mono_runtime_invoke"))return (void*)invoke;
 exit(34);
}
int main(int argc,char **argv){
 if(argc!=2)return 35;mode=argv[1];
 struct JNINativeInterface_ api={0};api.ExceptionCheck=check;api.ExceptionClear=clear;api.NewGlobalRef=global;
 api.DeleteGlobalRef=drop;api.DeleteLocalRef=drop;api.NewStringUTF=string;api.GetArrayLength=length;
 api.GetByteArrayElements=elements;api.ReleaseByteArrayElements=release;api.GetStaticMethodID=method;
 api.CallStaticBooleanMethod=boolean_call;api.CallStaticVoidMethod=void_call;environment=&api;
 struct JNIInvokeInterface_ calls={0};calls.GetEnv=get_environment;JavaVM vm=&calls;
 if(JNI_OnLoad(&vm,0)!=JNI_VERSION_1_6)return 36;
 int success=Java_com_vocies61_marvelcosmic_EnhancedBridge_nativeStart(&environment,(jclass)1,expected_activity,(jbyteArray)2);
 if(!strcmp(mode,"success")) {
  if(!success || invokes!=1 || released!=1 || !marvel_ready(expected_activity) || !marvel_finish(expected_activity) || !marvel_fail_open(expected_activity) || ready!=1 || finished!=1 || failed!=1)return 37;
 }else if(!strcmp(mode,"managed-error")) {if(success || invokes!=1 || released!=1)return 38;}
 else {if(success || invokes!=0)return 39;}
 printf("PASS %s\n",mode);return 0;
}
