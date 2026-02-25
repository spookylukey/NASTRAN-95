/*
 * Fork-based NASTRAN execution for f2py.
 * 
 * Since NASTRAN calls EXIT() and STOP which would kill the Python process,
 * we run the actual Fortran solver in a forked child process. The parent
 * waits for the child to complete.
 *
 * We also provide overrides for _gfortran_exit_i4 and _gfortran_stop_*
 * that simply call _exit() to cleanly terminate the child process.
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>
#include <string.h>

/* Flag to indicate we're in the child process */
static int in_child_process = 0;

/* The actual NASTRAN solver entry point (Fortran) */
extern void nastran_solve_impl_(const char *inputf, const char *outputf,
                                 int *ireturn, int inputf_len, int outputf_len);

/* Fork-safe wrapper called from Python via f2py */
void nastran_solve_forked_(const char *inputf, const char *outputf,
                           int *ireturn, int inputf_len, int outputf_len) {
    pid_t pid = fork();
    
    if (pid < 0) {
        /* Fork failed */
        *ireturn = -99;
        return;
    }
    
    if (pid == 0) {
        /* Child process - run NASTRAN */
        in_child_process = 1;
        int ret = 0;
        nastran_solve_impl_(inputf, outputf, &ret, inputf_len, outputf_len);
        /* If we get here, NASTRAN returned normally (unlikely) */
        _exit(ret);
    }
    
    /* Parent process - wait for child */
    int status;
    waitpid(pid, &status, 0);
    
    if (WIFEXITED(status)) {
        *ireturn = WEXITSTATUS(status);
    } else {
        *ireturn = -1;
    }
}

/* Override gfortran EXIT intrinsic.
 * Use exit() (not _exit()) to flush Fortran I/O buffers. */
void _gfortran_exit_i4(int *status) {
    exit(status ? *status : 0);
}

/* Override gfortran STOP with string */
void _gfortran_stop_string(const char *msg, int len, int quiet) {
    exit(0);
}

/* Override gfortran STOP with numeric code */  
void _gfortran_stop_numeric(int code, int quiet) {
    exit(code);
}
