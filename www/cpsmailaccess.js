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

function addToSection() {
  // need to set up a max
  ToNode = document.getElementById('Tos');
  if (ToNode)
  {
    new_section = document.createElement("div");
    new_section.appendChild(document.createTextNode("will add more to sections"));
    last_node = getLastToNode();
    ToNode.appendChild(new_section);
  }

}

function removeToSection() {
  ToNode = document.getElementById('Tos');
  if (ToNode)
  {
    new_section = document.createElement("div");
    last_node = getLastToNode();
    ToNode.removeChild(new_section);
  }
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

function saveMessageDatas(EditorHTML)
{
  msg_subject = document.getElementById('msg_subject');
  msg_subject = msg_subject.value
  msg_body = EditorHTML;
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
    var body = "msg_subject="+msg_subject+"&msg_body="+msg_body;
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
    alert(xml.status);
  }
}


