// #include <stdio.h>
// #include <assert.h>

int main(int argc, char *argv[]) {
// void main() {

    // Line 1
    // int Cur_Vertical_Sep             = 1258;
    // int High_Confidence              = 1;
    // int Two_of_Three_Reports_Valid   = 0;
    // int Own_Tracked_Alt              = 897;
    // int Own_Tracked_Alt_Rate         = 174;
    // int Other_Tracked_Alt            = 7253;
    // int Alt_Layer_Value              = 1;
    // int Up_Separation                = 629;
    // int Down_Separation              = 500;
    // int Other_RAC                    = 0;
    // int Other_Capability             = 0;
    // int Climb_Inhibit                = 1;

    // Line 2
    // int Cur_Vertical_Sep             = 775;
    // int High_Confidence              = 1;
    // int Two_of_Three_Reports_Valid   = 1;
    // int Own_Tracked_Alt              = 942;
    // int Own_Tracked_Alt_Rate         = 311;
    // int Other_Tracked_Alt            = 1504;
    // int Alt_Layer_Value              = 1;
    // int Up_Separation                = 540;
    // int Down_Separation              = 500;
    // int Other_RAC                    = 1;
    // int Other_Capability             = 0;
    // int Climb_Inhibit                = 1;

    // Line 8
    int Cur_Vertical_Sep             = 798;
    int High_Confidence              = 1;
    int Two_of_Three_Reports_Valid   = 1;
    int Own_Tracked_Alt              = 2071;
    int Own_Tracked_Alt_Rate         = 49;
    int Other_Tracked_Alt            = 307;
    int Alt_Layer_Value              = 0;
    int Up_Separation                = 849;
    int Down_Separation              = 904;
    int Other_RAC                    = 1;
    int Other_Capability             = 2;
    int Climb_Inhibit                = 0;


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

    //printf("ALIM: %d\n", ALIM);

    int Inhibit_Biased_Climb;

    if (Climb_Inhibit != 0) {
        Inhibit_Biased_Climb = Up_Separation + 100;
    } else {
        Inhibit_Biased_Climb = Up_Separation;
    }
    //printf("Inhibit_Biased_Climb: %d\n", Inhibit_Biased_Climb);

    int enabled;
    if (High_Confidence != 0 && (Own_Tracked_Alt_Rate <= 600) && (Cur_Vertical_Sep > 600)) {
        enabled = 1;
    } else {
        enabled = 0;
    }
    //printf("enabled: %d\n", enabled);


    int tcas_equipped;
    if (Other_Capability == 1) {
        tcas_equipped = 1;
    } else {
        tcas_equipped = 0;
    }
    //printf("tcas_equipped: %d\n", tcas_equipped);


    int intent_not_known;
    if (Two_of_Three_Reports_Valid != 0 && (Other_RAC == 0)) {
        intent_not_known = 1;
    } else {
        intent_not_known = 0;
    }
    //printf("intent_not_known: %d\n", intent_not_known);

    int alt_sep = 0;

    if (enabled != 0 && ((tcas_equipped != 0 && intent_not_known != 0) || tcas_equipped == 0)) {
        int Own_Below_Threat;
        if (Own_Tracked_Alt < Other_Tracked_Alt) {
            Own_Below_Threat = 1;
        } else {
            Own_Below_Threat = 0;
        }
        //printf("Own_Below_Threat: %d\n", Own_Below_Threat);

        int Own_Above_Threat;
        if (Other_Tracked_Alt < Own_Tracked_Alt) {
            Own_Above_Threat = 1;
        } else {
            Own_Above_Threat = 0;
        }
        //printf("Own_Above_Threat: %d\n", Own_Above_Threat);

        int upward_preferred;
        if (Inhibit_Biased_Climb > Down_Separation) {
            upward_preferred = 1;
        } else {
            upward_preferred = 0;
        }
        //printf("upward_preferred: %d\n", upward_preferred);

        int Non_Crossing_Biased_Climb;
        if (upward_preferred != 0) {
            if ((Own_Below_Threat == 0) || (Own_Below_Threat != 0 && !(Down_Separation >= ALIM))) {
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
        //printf("Non_Crossing_Biased_Climb: %d\n", Non_Crossing_Biased_Climb);

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
        //printf("Non_Crossing_Biased_Descend: %d\n", Non_Crossing_Biased_Descend);

        int need_upward_RA;
        if (Non_Crossing_Biased_Climb != 0 && Own_Below_Threat != 0) {
            need_upward_RA = 1;
        } else {
            need_upward_RA = 0;
        }
        //printf("need_upward_RA: %d\n", need_upward_RA);
       
        int need_downward_RA;
        if (Non_Crossing_Biased_Descend != 0 && Own_Above_Threat != 0) {
            need_downward_RA = 1;
        } else {
            need_downward_RA = 0;
        }
        //printf("need_downward_RA: %d\n", need_downward_RA);

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
        // printf("alt_sep: %d\n", alt_sep);
    }
    
    assert(alt_sep == 2);
}