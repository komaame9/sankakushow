// 💡 APIのベースURLを定義
const API_BASE_URL = "http://localhost:8000/save"; 

// 拡張機能がインストールされたときにコンテキストメニューを作成
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "sendImageUrl", // メニューアイテムの一意なID
    title: "sankakushowに送る", // メニューに表示されるテキスト
    contexts: ["image"] // 'image'コンテキストでのみ表示
  });
  console.log('Context menu created.');
});

// メニューアイテムがクリックされたときの処理
chrome.contextMenus.onClicked.addListener((info, tab) => {
  // クリックされたのが画像で、かつメニューIDが一致するか確認
  if (info.menuItemId === "sendImageUrl" && info.srcUrl) {
    const imageUrl = info.srcUrl;
    
    // URLSearchParamsを使ってクエリパラメータを構築
    const params = new URLSearchParams({
      url: imageUrl,
    });
    
    const fullApiUrl = `${API_BASE_URL}?${params.toString()}`;
    
    console.log('Sending GET request to:', fullApiUrl);

    // REST APIにGETリクエストを発行
    fetch(fullApiUrl, {
      method: 'GET',
      headers: {
        // 必要に応じて認証ヘッダーを追加
      }
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      console.log('REST API Success:', data);
      
      // 成功通知
      chrome.notifications.create({
        type: 'basic',
        title: '✅ 成功',
        message: `APIからの応答: ${JSON.stringify(data).substring(0, 100)}...`
      });

      // 💡 【追加】API成功時にタブが存在していれば閉じる
      if (tab && tab.id) {
        chrome.tabs.remove(tab.id, () => {
          console.log(`Tab ${tab.id} closed successfully.`);
        });
      }
    })
    .catch(error => {
      console.error('REST API Error:', error);
      
      // 失敗通知
      chrome.notifications.create({
        type: 'basic',
        title: '❌ 失敗',
        message: `画像の送信中にエラーが発生しました: ${error.message}`
      });
    });
  }
});