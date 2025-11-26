#include <stdio.h>
#include <assert.h>

int main(int argc, char *argv[]) {

    // INPUTS

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

    if (Climb_Inhibit != 0) {
        Inhibit_Biased_Climb = Up_Separation + 100;
    } else {
        Inhibit_Biased_Climb = Up_Separation;
    }

    int enabled;
    if (High_Confidence != 0 && (Own_Tracked_Alt_Rate <= 600) && (Cur_Vertical_Sep > 600)) {
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
    if (Two_of_Three_Reports_Valid != 0 && (Other_RAC == 0)) {
        intent_not_known = 1;
    } else {
        intent_not_known = 0;
    }

    int alt_sep = 0;

    if (enabled != 0 && ((tcas_equipped != 0 && intent_not_known != 0) || tcas_equipped == 0)) {
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

        int upward_preferred;
        if (Inhibit_Biased_Climb > Down_Separation) {
            upward_preferred = 1;
        } else {
            upward_preferred = 0;
        }

        int Non_Crossing_Biased_Climb;
        if (upward_preferred != 0) {
            if ((Own_Below_Threat == 0) || (Own_Below_Threat != 0 && !(Down_Separation >= ALIM))) {
                Non_Crossing_Biased_Climb = 1;
            } else {
                Non_Crossing_Biased_Climb = 0; 
            }
        } else {
            if (Own_Above_Threat != 0 && (Cur_Vertical_Sep >= 300) && (Up_Separation >= ALIM)) {
                Non_Crossing_Biased_Climb = 1;
            } else {
                Non_Crossing_Biased_Climb = 0;
            }
        }

        int Non_Crossing_Biased_Descend;
        if (upward_preferred != 0) {
            if (Own_Below_Threat != 0 && (Cur_Vertical_Sep >= 300) && (Down_Separation >= ALIM)) {
                Non_Crossing_Biased_Descend = 1;
            } else {
                Non_Crossing_Biased_Descend = 0;
            }
        } else {
            if ((Own_Above_Threat == 0) || (Own_Above_Threat != 0 && (Up_Separation >= ALIM))) {
                Non_Crossing_Biased_Descend = 1;
            } else {
                Non_Crossing_Biased_Descend = 0;
            }
        }

        int need_upward_RA;
        if (Non_Crossing_Biased_Climb != 0 && Own_Below_Threat != 0) {
            need_upward_RA = 1;
        } else {
            need_upward_RA = 0;
        }
       
        int need_downward_RA;
        if (Non_Crossing_Biased_Descend != 0 && Own_Above_Threat != 0) {
            need_downward_RA = 1;
        } else {
            need_downward_RA = 0;
        }

        if (need_upward_RA != 0 && need_downward_RA != 0) {
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

    // OUTPUT
}
