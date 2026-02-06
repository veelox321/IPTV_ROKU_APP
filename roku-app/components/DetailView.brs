sub init()
  m.poster = m.top.findNode("poster")
  m.title = m.top.findNode("title")
  m.description = m.top.findNode("description")
  m.duration = m.top.findNode("duration")
  m.genre = m.top.findNode("genre")
  m.rating = m.top.findNode("rating")
  m.top.observeField("contentItem", "onContentItem")
end sub

sub onContentItem()
  item = m.top.contentItem
  if item = invalid then return
  m.title.text = item.title
  m.description.text = item.description
  m.duration.text = item.duration
  m.genre.text = item.genre
  m.rating.text = item.rating
  if item.hdPosterUrl <> invalid
    m.poster.uri = item.hdPosterUrl
  end if
end sub
