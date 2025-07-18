gantiID = function (currentId, newId) {
  for (var i = 0; i < form.fields.length; i++) {
    if (form.fields[i].id == currentId) {
      form.fields[i].id = newId;
      jQuery("#field_" + currentId).attr("id", "field_" + newId);
      return "Bahalap Wal, Success!";
    }
  }
  return "Gagal!";
};
