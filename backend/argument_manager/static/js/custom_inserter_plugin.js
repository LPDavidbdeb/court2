tinymce.PluginManager.add('custom_inserter', function(editor, url) {
    editor.ui.registry.addMenuButton('custom_inserter', {
        icon: 'bookmark',
        tooltip: 'Insert Evidence',
        fetch: function(callback) {
            fetch('/arguments/ajax/all-quotes-for-tinymce/')
                .then(response => response.json())
                .then(data => {
                    const menuItems = [];
                    for (const type in data) {
                        const subMenuItems = data[type].map(item => ({
                            type: 'menuitem',
                            text: item.title,
                            onAction: function() {
                                editor.insertContent(item.value);
                            }
                        }));
                        menuItems.push({
                            type: 'nestedmenuitem',
                            text: type,
                            getSubmenuItems: function() {
                                return subMenuItems;
                            }
                        });
                    }
                    callback(menuItems);
                })
                .catch(error => {
                    console.error('Error fetching quotes for TinyMCE:', error);
                    callback([]);
                });
        }
    });

    return {
        getMetadata: function() {
            return {
                name: 'Custom Inserter',
                url: 'https://example.com'
            };
        }
    };
});
