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