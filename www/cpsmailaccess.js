/*
(C) Copyright 2003 Nuxeo SARL <http://nuxeo.com>
Author: Tarek Ziadé <tz@nuxeo.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License version 2 as published
by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
02111-1307, USA.
*/

/* Javascript functions used for the webmail

*/

/*
  changes the icon that is in front of subject header (+ or-)
*/
function switchMailHeadersState()
{
  node = document.getElementById("mailMoreInfos");
  img_node = document.getElementById("imgMailMoreInfos");

  if (node.style.display == "none")
  {
    node.style.display = "block";
    img_node.src = "cpsma_lessinfos.png";
  }
  else
  {
    node.style.display = "none";
    img_node.src = "cpsma_moreinfos.png";
  }
}

/*
  changes the icon that is in front of a tree folder (+ or -)
*/
function switchFolderState(id)
{
  node = document.getElementById(id);
  img_node = document.getElementById("img_"+id);

  if (node.style.display == "none")
  {
    node.style.display = "block";
    img_node.src = img_node.src.replace("plus", "minus")
  }
  else
  {
    node.style.display = "none";
    img_node.src = img_node.src.replace("minus", "plus")
  }
}

/*
  delay
*/
function delay(ms)
{
  then = new Date().getTime();
  now = then;
  while((now-then)<gap)
  {
    now = new Date().getTime();
  }
}

/*
  saves datas using XmlHttpRequest
*/
function saveMessageDatas()
{
  msg_subject = document.getElementById('msg_subject');
  msg_subject = msg_subject.value;

  msg_body = document.getElementById('msg_body');
  msg_body = msg_body.value;

  msg_to = document.getElementById('msg_to');
  msg_to = msg_to.value;

  msg_cc = document.getElementById('msg_cc');
  msg_cc = msg_cc.value;

  msg_bcc = document.getElementById('msg_bcc');
  msg_bcc = msg_bcc.value;

  Cc = document.getElementById('Cc');
  if (Cc.style.visibility == 'hidden')
  {
    cc_on = "0";
  }
  else
  {
    cc_on = "1";
  }

  BCc = document.getElementById('BCc');

  if (BCc.style.visibility == 'hidden')
  {
    bcc_on =  "0";
  }
  else
  {
    bcc_on = "1";
  }

  Attach = document.getElementById('attacher');

  if (Attach.style.visibility == 'hidden')
  {
    attacher_on =  "0";
  }
  else
  {
    attacher_on = "1";
  }

  if(window.XMLHttpRequest) // Firefox
    xml = new XMLHttpRequest();
  else if(window.ActiveXObject) // Internet Explorer
    xml = new ActiveXObject("Microsoft.XMLHTTP");
  else
  {
    // XMLHttpRequest not supported
  }
  if (xml)
  {
    url = "saveMessageForm.html";
    status = 503;
    msg_body = escape(msg_body);
    msg_subject = escape(msg_subject);
    msg_to = escape(msg_to);
    msg_cc = escape(msg_cc);
    msg_bcc = escape(msg_bcc);

    var body = "attacher_on="+attacher_on+"&cc_on="+cc_on+"&bcc_on="+bcc_on+"&msg_subject="+msg_subject+"&msg_body="+msg_body+"&msg_to="+msg_to+"&msg_cc="+msg_cc+"&msg_bcc="+msg_bcc
    i = 0;
    while ((status == 503) && (i<10))
    {
      xml.open("POST", url, false);
      xml.setRequestHeader("Content-type","application/x-www-form-urlencoded");
      xml.send(body);
      status = xml.status;
      if (status == 503)
      {
        i++;
        delay(200);
      }
    }
  }
}

/*
  hidden, visible
*/
function toggleElementVisibility(id)
{
  element = document.getElementById(id);

  if (element)
  {
    if (element.className == "hidden_part")
    {
      element.className = "not_hidden_part";
      element.style.visibility = "visible";
    }
    else
    {
      element.className = "hidden_part";
      element.style.visibility = "hidden";
    }
  }
}

/*
  Will popup the recipient picker window
*/
function popupRecipientPicker()
 {
    var args;
    url = "selectRecipients.html";
    popup = window.open(url, '_blank', 'toolbar=0, scrollbars=1, location=0, statusbar=0, menubar=0, resizable=1, dependent=1, width=500, height=500');
    if(!popup.opener)
        popup.opener = window;
}

/*
  Will popup a message if the text gets too big,given a max_size
  and a message to pop
*/
function controlInputSize(ob, max_size, evt, warning_message)
{
  if ((evt.keyCode == 8) || (evt.keyCode == 46) ||
      (evt.keyCode == 36) || (evt.keyCode == 37) ||
      (evt.keyCode == 35) || (ob.value.length == 0)
      )
  {
    return;
  }
  len = ob.value.length;
  if (len>max_size)
  {
    alert(warning_message);
    ob.value = ob.value.substring(0, max_size-1);
  }
}

/*
  Truncate a span content, given a max size
*/
function truncateFields(max_size)
{
  elements = document.getElementsByTagName("span");
  for (i=0; i<elements.length; i++)
  {
    element = elements[i];
    if (element.className == "truncable")
    {
      if (element.innerHTML.length>max_size)
      {
        element.innerHTML = element.innerHTML.substring(0, max_size-3) + '...'
      }
    }
  }
}

/*
  Hand look whatever is the navigator
*/
function setCursor(obj)
{
  if (navigator.appName == "Microsoft Internet Explorer"
            && navigator.appVersion.indexOf("5.") >= 0)
  {
    isIE = true;
  }
  // For some reason, appVersion returns 5 for Netscape 6.2 ...
  else if (navigator.appName == "Netscape"
          && navigator.appVersion.indexOf("5.") >= 0)
  {
    isIE = false;
  }
  else
    isIE = false;

  // Change the mouse cursor to hand or pointer
  if (isIE)
    obj.style.cursor = "hand";
  else
    obj.style.cursor = "pointer";
}