# Makefile for NASTRAN-95
#
# Usage:
#   make          — compile and link nastrn
#   make clean    — remove object files and binary

FC      = gfortran
FLAGS   = -std=legacy -fno-range-check -w -fallow-argument-mismatch \
          -fallow-invalid-boz -fno-automatic

SRC_DIRS = src_mis src_mds src_bd src_bin
SOURCES  = $(foreach d,$(SRC_DIRS),$(wildcard $(d)/*.f)) stubs.f
OBJECTS  = $(patsubst %.f,%.o,$(notdir $(SOURCES)))

# chkfil.f has its own PROGRAM main — exclude from link
LINK_OBJS = $(filter-out chkfil.o,$(OBJECTS))

VPATH = $(SRC_DIRS)

.PHONY: all clean

all: nastrn

nastrn: $(LINK_OBJS)
	$(FC) $(FLAGS) -o $@ $^

%.o: %.f
	$(FC) -c $(FLAGS) -I. $< -o $@

clean:
	rm -f *.o nastrn
