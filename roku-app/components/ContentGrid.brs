sub init()
  m.rowList = m.top.findNode("rowList")
  m.rowList.observeField("itemSelected", "onItemSelected")
  m.top.observeField("gridContent", "onGridContent")
end sub

sub onGridContent()
  m.rowList.content = m.top.gridContent
end sub

sub onItemSelected()
  rowIndex = m.rowList.rowItemSelected[0]
  itemIndex = m.rowList.rowItemSelected[1]
  rowNode = m.rowList.content.getChild(rowIndex)
  if rowNode <> invalid
    selected = rowNode.getChild(itemIndex)
    m.top.selectedItem = selected
  end if
end sub
