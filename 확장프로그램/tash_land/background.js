chrome.storage.local.get('access_token', function(result) {
  console.log("Stored value is: ", result.myKey);
});