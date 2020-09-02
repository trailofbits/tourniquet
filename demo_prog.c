#include <stdio.h>
#include <string.h>
/*
 * Worlds easiest crackme
 * Copies the arg into the buff, and checks to see if the password is password.
 * You can either exploit the challenge or solve it by reversing the password
 *
 * This is a PoC of the automated patcher prototype
 *
 * It uses the MATE CPG to collect all globals, parameters, and local variables
 * to use in patch templates. It then tries to automatically fill in templates,
 * and pass a test suite.
 *
 * To prevent the exploit/crash, a plausible patch is to just delete the strcpy
 * statement. But deleting the strcpy statement ruins the rest of the program,
 * as you can no longer copy passwords into the password buffer. Having an
 * additional test with input "password" which normally should pass, and fails
 * when removing strcpy, prunes these plausible but incorrect patches.
 */
char *pass = "password";


//This function logs errors
void LogError() {
	printf("Error!\n");
}

int main(int argc, char *argv[]) {
	//By calling LogError (known error function) 
	//Our analysis understands that the path leading to return -1 
	//is an error, therefore mains error return sign <0 
	if (argc < 2) {
		LogError();
		return 1;
	}
  char buff[10];
  int buff_len = sizeof(buff);
  char *pov = argv[1];
  int len = strlen(argv[1]);
  if (buff_len == len) {
    printf("Buffer sizes are of similar length!\n");
  }
  // Possible patch, if (length_check) {..} else return error
  strcpy(buff, pov);
  if (strcmp(buff, pass) == 0) {
    return 0;
  }

  return 1;
}
