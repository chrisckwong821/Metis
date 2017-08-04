var restify = require('restify');
var builder = require('botbuilder');
var url = require('url');
var fs = require('fs');
var azure = require('botbuilder-azure');

var needle = require('needle'), //Speech-to-text
    ffmpeg = require('fluent-ffmpeg'),
    speechService = require('./speech-service.js');

// Setup Restify Server
var server = restify.createServer();
server.listen(process.env.port || process.env.PORT || 3978, function () {
    console.log('%s listening to %s', server.name, server.url);
});

// Create chat connector for communicating with the Bot Framework Service
var connector = new builder.ChatConnector({
    appId: process.env.MICROSOFT_APP_ID,
    appPassword: process.env.MICROSOFT_APP_PASSWORD
});

//Setup Azure Table
var tableName = 'metisbot';
var azureTableClient = new azure.AzureTableClient(tableName,"metisbot","b9YdNPfchtxl2HhmrRXMBQhnOb3F0jci7VfjzDdbcfnbN9LuhM8Q87BVrO9f2tpu+ElXgm/V5iXw9e/Pj95Vvg==");
var tableStorage = new azure.AzureBotStorage({ gzipData: false }, azureTableClient);

// Initialize a bot
var bot = new builder.UniversalBot(connector).set('storage', tableStorage);;

// Listen for messages from users 
server.post('/api/messages', connector.listen());

// LUIS Natural Language Processing
var recognizer = new builder.LuisRecognizer("https://westus.api.cognitive.microsoft.com/luis/v2.0/apps/0b06c54f-3ebf-4806-bc8b-da05908fc314?subscription-key=2c282b6ca94042ac891d9b66315517c3&staging=true&verbose=true&timezoneOffset=0&q=");
bot.recognizer(recognizer);

//=========================================================
// Bots Global Actions
//=========================================================

bot.beginDialogAction('help', '/help', { matches: /^help/i });

//=========================================================
// Listener
//=========================================================
// Do GET this endpoint to start a dialog proactively
server.get('/api/listener', function (req, res, next) {
    var query = url.parse(req.url, true).query;
    fs.readFile("file.bin", (err, data) => {
        if (err) console.log(err)
        else {
            var savedAddresses = { '123112': JSON.parse(data) };
            var customerAddress = savedAddresses[query.customerid];
            startProactiveDialog(customerAddress);
            res.send('triggered');
            next();
        }
    })
});

// initiate a dialog proactively 
function startProactiveDialog(address) {
    // new conversation address, copy without conversationId
    var newConversationAddress = Object.assign({}, address);
    delete newConversationAddress.conversation;
    delete newConversationAddress.id;

    bot.beginDialog(newConversationAddress, "*:/WelcomeExistingCustomer", null, function (err) {
        if (err) {
            // error ocurred while starting new conversation. Channel not supported?
            bot.send(new builder.Message()
                .text('This channel does not support this operation: ' + err.message)
                .address(address));
        }
    });
}

//=========================================================
// Bots Middleware
//=========================================================

bot.use({
    botbuilder: function (session, next) {
        if (hasAudioAttachment(session)) {
            session.sendTyping();
            getAudioStreamFromMessage(session.message, function (stream) {
                speechService.getTextFromAudioStream(stream)
                    .then(function (text) {
                        session.message.text = text;
                        next();
                    })
                    .catch(function (error) {
                        console.error(error);
                        next();
                    });
            });
        } else {
            next();
        }
    }
});

//=========================================================
// Bot Start
//=========================================================

// Send welcome when conversation with bot is started, by initiating the root dialog
bot.on('conversationUpdate', function (message) {
    if (message.membersAdded) {
        message.membersAdded.forEach(function (identity) {
            if (identity.id === message.address.bot.id) {
                bot.beginDialog(message.address, '/Greeting');
            }
        });
    }
});

//=========================================================
// Bots Dialogs
//=========================================================

// Receive messages from the user and respond by echoing each message back (prefixed with 'You said:')
bot.dialog('/', function (session) {
    session.sendTyping();
    session.endConversation("Sorry, I cannot answer that. That is beyond my capablities for now.", session.message.text);
});

// handle the proactive initiated dialog
bot.dialog('/WelcomeExistingCustomer', function (session, args, next) {
    session.sendTyping();
    session.endConversation('Hi %s, Welcome to Contoso Outfitters! How can I be of help?',session.message.user.name);
});

bot.dialog('/help', function (session) {
    session.sendTyping();
    session.endConversation('An assistant will come right over to help you :)');
});

bot.dialog('/Greeting', function (session, args) {
    fs.writeFile("file.bin", JSON.stringify(session.message.address), 'binary', (err) => {
        if (err) console.log(err)
        else console.log('File saved')
    })
    session.sendTyping();
    session.endConversation('Hey %s!', session.message.user.name);
}).triggerAction({
    matches: 'greeting'
    });

bot.dialog('/ThanksReply', function (session, args) {
    session.sendTyping();
    session.endConversation('My Pleasure! :)');
}).triggerAction({
    matches: 'thanks'
});

bot.dialog('/PurchaseHistory', function (session, args) {
    var msg = new builder.Message(session);
    msg.attachmentLayout(builder.AttachmentLayout.carousel)
    session.sendTyping();
    msg.attachments([
        new builder.HeroCard(session)
            .title("Silk-blend Polo Shirt")
            .subtitle("Contoso Outfitters | Item Nr. 0443860009")
            .text("Dark Blue | Size Large | Quantity: 02")
            .images([builder.CardImage.create(session, 'http://lp2.hm.com/hmprod?set=source[/environment/2017/8VO_0205_009R.jpg],width[3462],height[4048],y[-1],type[FASHION_FRONT]&hmver=0&call=url[file:/product/main]')]),
        new builder.HeroCard(session)
            .title("COD Chinese Jacket")
            .subtitle("Clothes of Desire | Piece 001 ")
            .text("Indigo 11.50 | Natural Dye  | Size Medium | Quantity: 01")
            .images([builder.CardImage.create(session, 'https://cdn.shopify.com/s/files/1/0738/6935/products/02-04_1024x1024.jpg?v=1452683765')]),
        new builder.HeroCard(session)
            .title("Grandad shirt Regular fit")
            .subtitle("Azure Wears | Catalogue 41233112")
            .text("Dark Blue | Size Large | Quantity: 01")
            .images([builder.CardImage.create(session, 'http://lp2.hm.com/hmprod?set=source[/environment/2017/9BR_0424_048R.jpg],width[3946],height[4613],y[-1],type[FASHION_FRONT]&hmver=0&call=url[file:/product/main]')]),
        new builder.HeroCard(session)
            .title("Cotton Denim Jeans")
            .subtitle("Emperia | Style 01117017001 ")
            .text("Indigo | Size 34 | Quantity: 01")
            .images([builder.CardImage.create(session, 'http://images.e-giordano.com/productphoto/01117017001/81_2_1_1_0800_1000.jpg')]),  
    ]);
    session.send(msg).endDialog();
}).triggerAction({
    matches: 'wardrobe'
});

bot.dialog('/Recommendation', [
    function (session, args) {
        session.sendTyping();
        session.send("How about these?");
        msg = new builder.Message(session)
            .attachments([
                new builder.ThumbnailCard(session)
                    .title("Ace Embroidered Low-Top Sneaker")
                    .subtitle("Sometimes you want a splash of color with your white sneakers. This pair gives you that extra visual element with the brand's signature green-and-red stripe.")
                    .images([
                        builder.CardImage.create(session, "https://image.ibb.co/fw1wGa/LP_996x250_sneakerfever_hken.jpg")
                    ]).buttons([
                        builder.CardAction.imBack(session, "why these?", "Why?"),
                        builder.CardAction.imBack(session, "where can I find them?", "Where?")
                    ])
            ]);
        builder.Prompts.choice(session, msg, ["why these?", "where can I find them?"]);
    },
    function (session, results) {
        var msg;
        var reply = results.response.entity;
        switch (reply) {
            case 'why these?':
                msg = "Because:\r\n1. You seem to like a minimalistic design\r\n2. In accordance with your high reviews preference, these sneakers have an average rating of 4.23/5.00\r\n3. Your friend Chris bought the same and he reviewed them 5.0/5.0\r\n4. Your size is available in this store";
                break;
            case 'where can I find them?':
                msg = "They are available on the 2nd floor. An assistant will find you soon to offer help :)";
                break;
        }
        builder.Prompts.choice(session, msg, "thanks|where?", "button");
    },
    function (session, results) {
        var msg;
        var reply = results.response.entity;
        switch (reply) {
            case 'where?':
                msg = "They are available on the 2nd floor. An assistant is on the way to help you :)";
                break;
            case 'thanks':
                msg = "My pleasure :)";
                break;
        }
        session.endDialog(msg);
    }
]).triggerAction({ matches: 'recommendation' });


//=========================================================
// Utilities
//=========================================================

function hasAudioAttachment(session) {
    if (session.message.attachments) {
        return session.message.attachments.length > 0 &&
            (session.message.attachments[0].contentType === 'audio/wav' ||
                session.message.attachments[0].contentType === 'application/octet-stream' || session.message.attachments[0].contentType === 'audio/x-m4a' || session.message.attachments[0].contentType === 'audio/aac' || session.message.attachments[0].contentType === 'audio/vnd.dlna.adts');
    }
}

function getAudioStreamFromMessage(message, cb) {
    var headers = {};
    var attachment = message.attachments[0];
    if (checkRequiresToken(message)) {
        // The Skype attachment URLs are secured by JwtToken,
        // you should set the JwtToken of your bot as the authorization header for the GET request your bot initiates to fetch the image.
        // https://github.com/Microsoft/BotBuilder/issues/662
        connector.getAccessToken(function (error, token) {
            var tok = token;
            headers['Authorization'] = 'Bearer ' + token;
            headers['Content-Type'] = 'application/octet-stream';
        });
    }
    if (attachment.contentType === 'audio/x-m4a' || attachment.contentType === 'audio/aac' || attachment.contentType === 'audio/vnd.dlna.adts') {
        headers['Content-Type'] = attachment.contentType;
        var original = needle.get(attachment.contentUrl, { headers: headers, decode: false });
        original.on('finish', function () {
            var command = ffmpeg(original).toFormat('wav');
            var converted = command.pipe();
            command
                .on('error', function (err) {
                    console.log('An error occurred: ' + err.message);
                })
                .on('end', function () {
                    console.log('Processing finished !');
                    cb(converted);
                });
        });
    }
    else {
        headers['Content-Type'] = attachment.contentType;
        cb(needle.get(attachment.contentUrl, { headers: headers }));
    }
}

function checkRequiresToken(message) {
    return message.source === 'skype' || message.source === 'msteams';
}