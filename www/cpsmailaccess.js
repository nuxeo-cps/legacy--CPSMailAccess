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
  while (next) {
    node = next;
    next = document.getElementById('to'+String.valueOf(++i));
  }
  return node
}

function addToSection() {
  // need to set up a max
  ToNode = document.getElementById('Tos');
  if (ToNode) {
    new_section = document.createElement("div");
    new_section.appendChild(document.createTextNode("will add more to sections"));
    last_node = getLastToNode();
    ToNode.appendChild(new_section);
  }

}

function removeToSection() {
  ToNode = document.getElementById('Tos');
  if (ToNode) {
    new_section = document.createElement("div");
    last_node = getLastToNode();

    ToNode.removeChild(new_section);
  }
}

function saveMessageDatas() {
  // for mozilla, need to find the same for ie
  // we are saving just subject and body
  msg_subject = document.getElementById('msg_subject');

  // find how to extract  [object HTMLTextAreaElement] content to save it
  msg_body = document.getElementById('msg_body');

  url = "saveMessageForm?msg_subject=" + msg_subject.value + "&msg_body=" + msg_body

  var xml = new XMLHttpRequest();
  xml.open("GET", url,true);
  xml.send(null);

}


