/*
(C) Copyright 2003 Nuxeo SARL <http://nuxeo.com>
Author: Tarek Ziad� <tz@nuxeo.com>

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
EMPTY = "__#EMPTY#__";
var currentXMLObject = false;
var currentTranslateXMLObject = false;

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
    createCookie(id, "block");
    node.style.display = "block";
    img_node.src = img_node.src.replace("plus", "minus")
  }
  else
  {
    createCookie(id, "none");
    node.style.display = "none";
    img_node.src = img_node.src.replace("minus", "plus")
  }
}

/*
  reads the cookie to set up the tree
*/
function controlStates()
{
  var name_starts_with = "tree_";
  var ca = document.cookie.split(';');
  for(var i=0;i < ca.length;i++)
  {
    var c = ca[i];
    while (c.charAt(0)==' ')
      c = c.substring(1,c.length);
    if (c.indexOf(name_starts_with) == 0)
    {
      eq_index = c.indexOf("=");
      cookie_name = c.substring(0, eq_index);
      cookie_value = c.substring(eq_index+1, c.length);
      node = document.getElementById(cookie_name);
      if (node)
      {
        if (node.style.display !=  cookie_value)
        {
          switchFolderState(cookie_name);
        }
      }
    }
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
function createXMLObject()
{
  if (window.XMLHttpRequest) // Firefox
    xml = new XMLHttpRequest();
  else if (window.ActiveXObject) // Internet Explorer
    xml = new ActiveXObject("Microsoft.XMLHTTP");
  else
  {
    // XMLHttpRequest not supported
    xml = null;
  }
  return xml;
}

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

  try
  {
    Cc = document.getElementById('Cc');
    if (Cc.style.visibility == 'hidden')
    {
      cc_on = "0";
    }
    else
    {
      cc_on = "1";
    }
  }
  catch(err)
  {
    cc_on = "0";
  }
  try
  {
    BCc = document.getElementById('BCc');

    if (BCc.style.visibility == 'hidden')
    {
      bcc_on =  "0";
    }
    else
    {
      bcc_on = "1";
    }
  }
  catch(err)
  {
    bcc_on = "0";
  }

  try
  {
    Attach = document.getElementById('attacher');

    if (Attach.style.visibility == 'hidden')
    {
      attacher_on =  "0";
    }
    else
    {
      attacher_on = "1";
    }
  }
  catch(err)
  {
    attacher_on = "0";
  }

  currentXMLObject = createXMLObject();

  if (currentXMLObject)
  {
    url = "saveMessageForm.html";
    status = 503;
    equals = "=";

    var poster = new Array();

    poster.push(encodeURIComponent("attacher_on") + equals + encodeURIComponent(attacher_on));
    poster.push(encodeURIComponent("cc_on") + equals + encodeURIComponent(cc_on));
    poster.push(encodeURIComponent("bcc_on") + equals + encodeURIComponent(bcc_on));
    poster.push(encodeURIComponent("msg_subject") + equals + encodeURIComponent(msg_subject));
    poster.push(encodeURIComponent("msg_body") + equals + encodeURIComponent(msg_body));
    poster.push(encodeURIComponent("msg_to") + equals + encodeURIComponent(msg_to));
    poster.push(encodeURIComponent("msg_cc") + equals + encodeURIComponent(msg_cc));
    poster.push(encodeURIComponent("msg_bcc") + equals + encodeURIComponent(msg_bcc));

    poster = poster.join(encodeURIComponent("&"));

    i = 0;
    while ((status == 503) && (i<10))
    {
      currentXMLObject.open("POST", url, false);
      currentXMLObject.setRequestHeader("Content-Type",
                           "application/www-form-urlencoded; charset=utf-8");
      currentXMLObject.send(poster);
      status = currentXMLObject.status;
      if (status == 503)
      {
        i++;
        delay(200);
      }
    }
  }
  else
  {
    alert("operation not supported");
  }
}

/*
  hidden, visible
*/
function toggleElementVisibility(element_id)
{

  element = document.getElementById(element_id);

  if (element)
  {
    if (element.className.find("not_hidden_part") != -1)
    {

      element.className = element.className.replace("not_hidden_part", "hidden_part");
      element.style.visibility = "hidden";
    }
    else
    {

      if (element.className.find("hidden_part") != -1)
      {
        element.className = element.className.replace("hidden_part", "not_hidden_part");
      }
      else
      {
        element.className = element.className + " hidden_part";
      }

      element.style.visibility = "visible";
    }
  }
  else
  {
  }
}

function setMessage(msg)
{
  element = document.getElementById("java_msm");

  if (element)
  {
    element.innerHTML = msg;
    if (msg)
    {
      // showing it

      if (element.className.indexOf("not_hidden_part") == -1)
      {
        toggleElementVisibility("java_msm");

      }
    }
    else
    {

      // hiding it
      if (element.className.indexOf("not_hidden_part") != -1)
      {
        toggleElementVisibility("java_msm");
      }
    }
  }
}



function getValueFromInput(id)
{
  input_ob = document.getElementById(id);
  if (!input_ob)
  {
    return EMPTY;
  }
  value_ob = input_ob.value;
  if (value_ob == "")
  {
    return EMPTY;
  }
  else
  {
    return value_ob;
  }
}
// sends the message
function sendMessageResult()
{
  if (currentXMLObject.readyState == 4)
  {
    unWaitProcess();
    response = extractResponse(currentXMLObject.responseText);

    if (response == "cpsma_message_sent")
    {
      trans = translate(response);
    }
    else
    {
      trans = response;
    }

    setMessage(trans);

    if (response == "cpsma_message_sent")
    {
      if (came_from)
      {
        gotoUrl(came_from+"?msm=" + response);
      }
      else
      {
        clearEditor();
      }
    }
  }
  else
  {
    if (currentXMLObject.readyState==1)
    {
      // protecting from "double-send" and making screen changes
      waitProcess();

      // setting up msg
      element = document.getElementById("java_msm");
      element.className = element.className.replace("hidden_part", "not_hidden_part");
      element.style.visibility = "visible";
      element.innerHTML = "Sending the message...";
    }
  }
}

function waitProcess()
{
  element = document.getElementById("send");
  element.style.visibility = "hidden";
  element = document.getElementById("msg_body");
  element.className = element.className + " waiting_process";
  element = document.getElementById("msg_to");
  element.className = element.className + " waiting_process";
  element = document.getElementById("msg_subject");
  element.className = element.className + " waiting_process";
}

function unWaitProcess()
{
  element = document.getElementById("send");
  element.style.visibility = "visible";
  element = document.getElementById("msg_body");
  element.className = element.className.replace("waiting_process", "");
  element = document.getElementById("msg_to");
  element.className = element.className.replace("waiting_process", "");
  element = document.getElementById("msg_subject");
  element.className = element.className.replace("waiting_process", "");
}

function sendMessage()
{
  // reading values on the form
  came_from = getValueFromInput("came_from");
  if (came_from==EMPTY)
  {
    came_from = "";
  }
  msg_from = getValueFromInput("msg_from");
  msg_subject = getValueFromInput("msg_subject");
  msg_body = getValueFromInput("msg_body");
  msg_to = getValueFromInput("msg_to");
  msg_cc = getValueFromInput("msg_cc");
  msg_bcc = getValueFromInput("msg_bcc");

  // computing uri
  var poster = new Array();
  equals = "=";
  poster.push(encodeURIComponent("responsetype") + equals + encodeURIComponent("text"));
  poster.push(encodeURIComponent("msg_subject") + equals + encodeURIComponent(msg_subject));
  poster.push(encodeURIComponent("msg_body") + equals + encodeURIComponent(msg_body));
  poster.push(encodeURIComponent("msg_to") + equals + encodeURIComponent(msg_to));
  poster.push(encodeURIComponent("msg_cc") + equals + encodeURIComponent(msg_cc));
  poster.push(encodeURIComponent("msg_bcc") + equals + encodeURIComponent(msg_bcc));
  poster.push(encodeURIComponent("msg_from") + equals + encodeURIComponent(msg_from));
  poster = poster.join("&");

  // sending mail
  currentXMLObject = createXMLObject();

  if (xml)
  {
    url = "sendMessage.html";
    currentXMLObject.open("POST", url, true);
    currentXMLObject.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    currentXMLObject.onreadystatechange = sendMessageResult;
    try
    {
      currentXMLObject.send(poster);
    }
    catch(err)
    {
      alert("operation not supported");
    }
  }
  else
  {
    alert("operation not supported");
  }
  //gotoUrl("editAction.html?" + poster);
}

function translate(msg)
{
  txml = createXMLObject();

  if (txml)
  {
    url = "Localizer/default/gettext";
    status = 503;
    i = 0;
    while ((status == 503) && (i<10))
    {
      txml.open("POST", url, false);
      txml.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
      txml.send(encodeURIComponent("message")+"="+encodeURIComponent(msg));
      status = xml.status;
      if (status == 503)
      {
        i++;
        delay(200);
      }

    }
    alert(txml.responseText);
    res = extractResponse(txml.responseText);
    return res;
  }
  else
  {
    return msg;
  }
}

function extractResponse(response)
{
  start = response.indexOf("<body>", 0);
  if (start != -1)
  {
    start = start + "<body>".length + 1;
    end = response.indexOf("</body>", start) - 1;
    return response.substring(start, end);
  }
  else
  {
    return response;
  }
}

function clearEditor()
{
  msg_subject = document.getElementById("msg_subject");
  msg_body = document.getElementById("msg_body");
  msg_to = document.getElementById("msg_to");
  msg_cc = document.getElementById("msg_cc");
  msg_bcc = document.getElementById("msg_bcc");

  if (msg_to)
  {
    msg_to.value = "";
  }
  if (msg_body)
  {
    msg_body.value = "";
  }
  if (msg_cc)
  {
    msg_cc.value = "";
  }
  if (msg_bcc)
  {
    msg_bcc.value = "";
  }
  if (msg_subject)
  {
    msg_subject.value = "";
  }
}


/*
  Will popup the recipient picker window
*/
var parent_window;

function popupRecipientPicker()
 {
    saveMessageDatas();

    var args;
    url = "selectRecipients.html";
    popup = window.open(url, '_blank', 'toolbar=0, scrollbars=1, location=0, statusbar=0, menubar=0, resizable=1, dependent=1, width=500, height=450');
    if(!popup.opener)
        popup.opener = window;
}

function closeDirectoryPicker()
{
  // XXX can do better : insufllate changes in text areas
  window.opener.location.reload();
  window.close();
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
    if (element.className.indexOf("truncable") != -1)
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
  if (navigator.appName == "Microsoft Internet Explorer")
  {
    isIE = true;
  }
  else
    isIE = false;

  // Change the mouse cursor to hand or pointer
  if (isIE)
    obj.style.cursor = "hand";
  else
    obj.style.cursor = "pointer";
}


/*
    Cookies
*/
function createCookie(name, value, days)
{
  if (days)
  {
    var date = new Date();
    date.setTime(date.getTime()+(days*24*60*60*1000));
    var expires = "; expires="+date.toGMTString();
  }
  else
    var expires = "";
  document.cookie = name+"="+value+expires+"; path=/";
}

function readCookie(name)
{
  var nameEQ = name + "=";
  var ca = document.cookie.split(';');
  for(var i=0;i < ca.length;i++)
  {
    var c = ca[i];
    while (c.charAt(0)==' ')
      c = c.substring(1,c.length);
    if (c.indexOf(nameEQ) == 0)
      return c.substring(nameEQ.length,c.length);
  }
  return null;
}

function eraseCookie(name)
{
  createCookie(name,"",-1);
}

/*
  used to enable onclick to go to an url
*/

function gotoUrl(dest)
{
  self.location.href = dest;
}

/* setting up drag and drop things */
var Destinations = [];

function cellMove(selected_items, target_node)
{
  from = selected_items[0].id;
  to = target_node.id;
  url = "moveElement.html?from_place="+from+"&to_place="+ to
  gotoUrl(url);
}

function cellCheckMove(selected_items, target_node)
{
  return true;
}

function cellDrag(node)
{
  pd_setupDragUI(node, cellMove, cellCheckMove);
}


function cellDest(node)
{
  if (Destinations.push)
    Destinations.push(node);
  else
    Destinations = Destinations.concat([node]);
  pd_setupDropTarget(node, 1);

}

pd_node_setup['cellDrag'] = cellDrag;
pd_node_setup['cellDest'] = cellDest;


/* select all messages in content managment mode */
function selectAllMessages(object, select_all_value, deselect_all_value)
{
  if (object.value == select_all_value)
  {
    checkboxes = object.form.elements;

    for (var i=0; i < checkboxes.length; i++)
    {
      checkboxes[i].checked = true;
    }
    object.value = deselect_all_value;
  }
  else
  {
    checkboxes = object.form.elements;

    for (var i=0; i < checkboxes.length; i++)
    {
      checkboxes[i].checked = false;
    }
    object.value = select_all_value;
  }
}

