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

function getLastToNode () {
  i = 0;
  stri = String.valueOf(i);
  node = document.getElementById('to'+String.valueOf(i));
  next = node;
  while (next)
  {
    node = next;
    next = document.getElementById('to'+String.valueOf(++i));
  }
  return node
}

function delay(ms)
{
  then = new Date().getTime();
  now = then;
  while((now-then)<gap)
  {
    now = new Date().getTime();
  }
}

function saveMessageDatas()
{
  msg_subject = document.getElementById('msg_subject');
  msg_subject = msg_subject.value

  msg_body = document.getElementById('msg_body');
  msg_body = msg_body.innerHTML

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
    url = "saveMessageForm";
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

function toggleElementVisibility(id)
{
  element = document.getElementById(id);

  if (element)
  {
    if (element.className == "hidden_part")
    {
      element.className = "not_hidden_part";
      element.style.visibility = "visible"
    }
    else
    {
      element.className = "hidden_part";
      element.style.visibility = "hidden"
    }
  }

}

function popupRecipientPicker()
 {
    var args;
    url = "selectRecipients"
    popup = window.open(url, '_blank', 'toolbar=0, scrollbars=1, location=0, statusbar=0, menubar=0, resizable=1, dependent=1, width=400, height=300');
    if(!popup.opener)
        popup.opener = window;
}
