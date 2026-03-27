# Makefile for NASTRAN-95
#
# Usage:
#   make               — compile and link nastrn (Linux)
#   make nastrn.exe     — cross-compile for Windows (requires mingw-w64)
#   make clean          — remove object files and binaries

FC      = gfortran
FLAGS   = -std=legacy -fno-range-check -w -fallow-argument-mismatch \
          -fallow-invalid-boz -fno-automatic
LFLAGS  = -static-libgfortran -static-libgcc

SRC_DIRS = src_mis src_mds src_bd src_bin
SOURCES  = $(foreach d,$(SRC_DIRS),$(wildcard $(d)/*.f)) stubs.f
OBJECTS  = $(patsubst %.f,%.o,$(notdir $(SOURCES)))

# chkfil.f has its own PROGRAM main — exclude from link
LINK_OBJS = $(filter-out chkfil.o,$(OBJECTS))

VPATH = $(SRC_DIRS)

.PHONY: all clean nastrn.exe

all: nastrn

nastrn: $(LINK_OBJS)
	$(FC) $(FLAGS) $(LFLAGS) -o $@ $^

# Cross-compile for Windows using MinGW-w64.
# Fully static so the exe has no DLL dependencies beyond KERNEL32/msvcrt.
# MinGW auto-appends .exe, so `make nastrn` produces nastrn.exe.
nastrn.exe:
	$(MAKE) clean
	$(MAKE) FC=x86_64-w64-mingw32-gfortran LFLAGS="-static" nastrn
	@test -f nastrn.exe || mv nastrn nastrn.exe
	$(MAKE) clean

%.o: %.f
	$(FC) -c $(FLAGS) -I. $< -o $@

clean:
	rm -f *.o nastrn
