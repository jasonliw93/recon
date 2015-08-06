/*
Copyright(c) 2013-2014 Ilya Kreymer. Released under the GNU General Public License.

This file is part of pywb, https://github.com/ikreymer/pywb

    pywb is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    pywb is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with pywb.  If not, see <http://www.gnu.org/licenses/>.
 */
window.parent.myfunction( wbinfo.timestamp); 

function __WbJsInit() {


function init_banner() {
    var PLAIN_BANNER_ID = "_wb_plain_banner";
    var FRAME_BANNER_ID = "_wb_frame_top_banner";
    var bid;

    if (window.top != window.self) {
        return;
    }

    if (wbinfo.is_frame) {
        bid = FRAME_BANNER_ID;
    } else {
        bid = PLAIN_BANNER_ID;
    }

    if (document.getElementById(bid) != null) {
        return;
    }
    
    _wb_js.create_banner_element(bid);
}

this.banner_labels = {LOADING_MSG: "Loading...",
                      REPLAY_MSG: "This is an <b>archived</b> page from ",
                      LIVE_MSG: "This is a <b>live</b> page loaded on "};

this.create_banner_element = function() {
    // No banner by default
    return null;
}

this.ts_to_date = function(ts, is_gmt)
{
    if (ts.length < 14) {
        return ts;
    }
    
    var datestr = (ts.substring(0, 4) + "-" + 
                  ts.substring(4, 6) + "-" +
                  ts.substring(6, 8) + "T" +
                  ts.substring(8, 10) + ":" +
                  ts.substring(10, 12) + ":" +
                  ts.substring(12, 14) + "-00:00");
    
    var date = new Date(datestr);
    if (is_gmt) {
        return date.toGMTString();
    } else {
        return date.toLocaleString();
    }
}

function add_event(name, func, object) {
    if (object.addEventListener) {
        object.addEventListener(name, func);
        return true;
    } else if (object.attachEvent) {
        object.attachEvent("on" + name, func);
        return true;
    } else {
        return false;
    }
}

function remove_event(name, func, object) {
    if (object.removeEventListener) {
        object.removeEventListener(name, func);
        return true;
    } else if (object.detachEvent) {
        object.detachEvent("on" + name, func);
        return true;
    } else {
        return false;
    }
}

function notify_top() {
    if (window.parent != window.top) {
        return;
    }

    if (!window.WB_wombat_location) {
        return;
    }

    if (typeof(window.WB_wombat_location.href) != "string") {
        return;
    }

    window.parent.update_wb_url(window.WB_wombat_location.href,
                                wbinfo.timestamp,
                                wbinfo.is_live);

    remove_event("readystatechange", notify_top, document);
}

this.load = function() {
    if ((window.self == window.top) && wbinfo) {
        if (wbinfo.top_url && (window.location.href != wbinfo.top_url) && wbinfo.mod != "bn_") {
            // Auto-redirect to top frame
            window.location.replace(wbinfo.top_url);
        } else {
            // Init Banner (no frame or top frame)
            add_event("readystatechange", init_banner, document);
        }
    } else if (window.self != window.parent && window.parent.update_wb_url) {
        add_event("readystatechange", notify_top, document);
    }
}

};


_wb_js = new __WbJsInit();