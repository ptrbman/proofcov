#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {

    int Cur_Vertical_Sep       = atoi(argv[1]);
    int High_Confidence       = atoi(argv[2]);
    int Two_of_Three_Reports_Valid = atoi(argv[3]);
    int Own_Tracked_Alt        = atoi(argv[4]);
    int Own_Tracked_Alt_Rate   = atoi(argv[5]);
    int Other_Tracked_Alt      = atoi(argv[6]);
    int Alt_Layer_Value        = atoi(argv[7]);
    int Up_Separation          = atoi(argv[8]);
    int Down_Separation        = atoi(argv[9]);
    int Other_RAC              = atoi(argv[10]);
    int Other_Capability       = atoi(argv[11]);
    int Climb_Inhibit          = atoi(argv[12]);

    // Inline ALIM()
    int ALIM;
    if (Alt_Layer_Value == 0) {
        ALIM = 400;
    } else {
        if (Alt_Layer_Value == 1) {
            ALIM = 500;
        } else {
            if (Alt_Layer_Value == 2) {
                ALIM = 640;
            } else {
                ALIM = 740;
            }
        }
    }

    int Inhibit_Biased_Climb;

    if (Climb_Inhibit) {
        Inhibit_Biased_Climb = Up_Separation + 100;
    } else {
        Inhibit_Biased_Climb = Up_Separation;
    }

    int enabled;
    if (High_Confidence && (Own_Tracked_Alt_Rate <= 600) && (Cur_Vertical_Sep > 600)) {
        enabled = 1;
    } else {
        enabled = 0;
    }


    int tcas_equipped;
    if (Other_Capability == 1) {
        tcas_equipped = 1;
    } else {
        tcas_equipped = 0;
    }

    int intent_not_known;
    if (Two_of_Three_Reports_Valid && (Other_RAC == 0)) {
        intent_not_known = 1;
    } else {
        intent_not_known = 0;
    }

    int alt_sep = 0;

    if (enabled && ((tcas_equipped && intent_not_known) || !tcas_equipped)) {
        // Inline Own_Below_Threat() and Own_Above_Threat(
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

        // Inline Non_Crossing_Biased_Climb()
        int upward_preferred;
        if (Inhibit_Biased_Climb > Down_Separation) {
            upward_preferred = 1;
        } else {
            upward_preferred = 0;
        }

        int Non_Crossing_Biased_Climb;
        if (upward_preferred) {
            if ((!Own_Below_Threat) || (Own_Below_Threat && !(Down_Separation >= ALIM))) {
                Non_Crossing_Biased_Climb = 1;
            } else {
                Non_Crossing_Biased_Climb = 0;
            }
        } else {
            if (Own_Above_Threat && (Cur_Vertical_Sep >= 300) && (Up_Separation >= ALIM)) {
                Non_Crossing_Biased_Climb = 1;
            } else {
                Non_Crossing_Biased_Climb = 0;
            }
        }

        // Inline Non_Crossing_Biased_Descend()
        int Non_Crossing_Biased_Descend;
        if (upward_preferred) {
            if (Own_Below_Threat && (Cur_Vertical_Sep >= 300) && (Down_Separation >= ALIM)) {
                Non_Crossing_Biased_Descend = 1;
            } else {
                Non_Crossing_Biased_Descend = 0;
            }
        } else {
            if ((!Own_Above_Threat) || (Own_Above_Threat && (Up_Separation >= ALIM))) {
                Non_Crossing_Biased_Descend = 1;
            } else {
                Non_Crossing_Biased_Descend = 0;
            }
        }

        int need_upward_RA;
        if (Non_Crossing_Biased_Climb && Own_Below_Threat) {
            need_upward_RA = 1;
        } else {
            need_upward_RA = 0;
        }
       
        int need_downward_RA;
        if (Non_Crossing_Biased_Descend && Own_Above_Threat) {
            need_downward_RA = 1;
        } else {
            need_downward_RA = 0;
        }

        if (need_upward_RA && need_downward_RA) {
            alt_sep = 0;
        } else if (need_upward_RA) {
            alt_sep = 1;
        } else if (need_downward_RA) {
            alt_sep = 2;
        } else {
            alt_sep = 0;
        }
    }

    fprintf(stdout, "%d\n", alt_sep);
    return 0;
}