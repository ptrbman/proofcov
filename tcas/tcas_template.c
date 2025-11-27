
/*  -*- Last-Edit:  Fri Jan 29 11:13:27 1993 by Tarak S. Goradia; -*- */
/* $Log: tcas.c,v $
 * Revision 1.2  1993/03/12  19:29:50  foster
 * Correct logic bug which didn't allow output of 2 - hf
 * */

#include <stdio.h>
#include <stdlib.h>


void main(int argc, char *argv[]) {
    int Cur_Vertical_Sep = atoi(argv[1]);
    int High_Confidence = atoi(argv[2]);
    int Two_of_Three_Reports_Valid = atoi(argv[3]);
    int Own_Tracked_Alt = atoi(argv[4]);
    int Own_Tracked_Alt_Rate = atoi(argv[5]);
    int Other_Tracked_Alt = atoi(argv[6]);
    int Alt_Layer_Value = atoi(argv[7]);
    int Up_Separation = atoi(argv[8]);
    int Down_Separation = atoi(argv[9]);
    int Other_RAC = atoi(argv[10]);
    int Other_Capability = atoi(argv[11]);
    int Climb_Inhibit = atoi(argv[12]);


    int ALIM = 0;
    if (Alt_Layer_Value == 0) {
        ALIM = 400;
    } else {
        if (Alt_Layer_Value == 1) {
            ALIM = 500;
        } else {
            if (Alt_Layer_Value == 2) {
                ALIM = 640;
            } else { 
                if (Alt_Layer_Value == 3) {
                    ALIM = 740;
                }
            }
        }
    }

    int enabled, tcas_equipped, intent_not_known;
    int need_upward_RA, need_downward_RA;
    int alt_sep;

    if ((High_Confidence != 0) && (Own_Tracked_Alt_Rate <= 600) && (Cur_Vertical_Sep > 600)) {
        enabled = 1;
    } else {
        enabled = 0;
    }
   
    if (Other_Capability == 1) {
        tcas_equipped = 1;
    } else {
        tcas_equipped = 0;
    }

    if (Two_of_Three_Reports_Valid != 0 && (Other_RAC == 0)) {
        intent_not_known = 1;
    } else {
        intent_not_known = 0;
    }
    
    alt_sep = 0;
    
    if ((enabled != 0) && (((tcas_equipped != 0) && (intent_not_known != 0)) || !(tcas_equipped != 0))) {

        int Non_Crossing_Biased_Climb;
            
        int upward_preferred;
        int upward_crossing_situation;
        int result;

        if (Climb_Inhibit != 0) {
            if (Up_Separation + 100 > Down_Separation   ) {
                upward_preferred = 1;
            } else {
                upward_preferred = 0;
            }
        } else {
            if (Up_Separation > Down_Separation   ) {
                upward_preferred = 1;
            } else {
                upward_preferred = 0;
            }
        }

        int Own_Below_Threat;
        if (Own_Tracked_Alt < Other_Tracked_Alt) {
            Own_Below_Threat = 1;
        } else {
            Own_Below_Threat = 0;
        }

        int Own_Above_Threat;
        if (Other_Tracked_Alt < Own_Tracked_Alt) {
            Own_Above_Threat = 1;
        } else {
            Own_Above_Threat = 0;
        }

        if (upward_preferred != 0)
        {
            if (!(Own_Below_Threat != 0) || ((Own_Below_Threat != 0) && (!(Down_Separation >= ALIM)))) {
                result = 1;
            } else {
                result = 0;
            }
        } else {	
            if ((Own_Above_Threat != 0) && (Cur_Vertical_Sep >= 300) && (Up_Separation >= ALIM)) {
                result = 1;
            } else {
                result = 0;
            }
        }

        Non_Crossing_Biased_Climb = result;

        if (Non_Crossing_Biased_Climb != 0 && Own_Below_Threat != 0) {
            need_upward_RA = 1;
        } else {
            need_upward_RA = 0;
        }

        int Non_Crossing_Biased_Descend;

        if (Climb_Inhibit != 0) {
            if (Up_Separation + 100 > Down_Separation) {
                upward_preferred = 1;
            } else {
                upward_preferred = 0;
            }
        } else {
            if (Up_Separation > Down_Separation) {
                upward_preferred = 1;
            } else {
                upward_preferred = 0;
            }
        }

        if (upward_preferred != 0)
        {
            if ((Own_Below_Threat != 0) && (Cur_Vertical_Sep >= 300) && (Down_Separation >= ALIM)) {
                result = 1;
            } else {
                result = 0;
            }
        } else {
            if (!(Own_Above_Threat != 0) || ((Own_Above_Threat != 0) && (Up_Separation >= ALIM))) {
                result = 1;
            } else {
                result = 0;
            }
        }

        Non_Crossing_Biased_Descend = result;

        if (Non_Crossing_Biased_Descend != 0 && Own_Above_Threat != 0) {
            need_downward_RA = 1;
        } else {
            need_downward_RA = 0;
        }

        if ((need_upward_RA != 0) && (need_downward_RA != 0)) {
            alt_sep = 0;
        } else { 
            if (need_upward_RA != 0) {
                alt_sep = 1;
            } else { 
                if (need_downward_RA != 0) {
                    alt_sep = 2;
                } else {
                    alt_sep = 0;
                }
            }
        }
    }
 
   
    int result = alt_sep;

    fprintf(stdout, "%d\n", result);
    exit(0);
}