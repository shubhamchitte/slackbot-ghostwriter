"""
Module 4: Interaction Handler
Presents suggestions as interactive Slack cards using Block Kit.
Handles button clicks and modal interactions.
"""

import logging
from typing import Dict
from datetime import datetime
from slack_listener import SlackListener
from storage import Storage

logger = logging.getLogger(__name__)


class InteractionHandler:
    """Handles Slack Block Kit interactions for suggestion cards."""
    
    def __init__(self, slack_listener: SlackListener, storage: Storage):
        """
        Initialize interaction handler.
        
        Args:
            slack_listener: SlackListener instance
            storage: Storage instance
            ghostwriter: Optional Ghostwriter instance (for retries)
        """
        self.slack = slack_listener
        self.storage = storage
        self.ghostwriter = None  # Will be set by main.py
        
        # Register button handlers
        self._register_handlers()
        
        logger.info("Interaction handler initialized")
    
    def _register_handlers(self):
        """Register handlers for button interactions and modals."""
        
        @self.slack.app.action("edit_suggestion")
        def handle_edit(ack, body, client):
            """Handle Edit button click."""
            ack()
            
            try:
                buffer_id = body['actions'][0]['value']
                suggestion = self.storage.get_suggestion(buffer_id)
                
                if not suggestion:
                    logger.error(f"Suggestion not found: {buffer_id}")
                    return
                
                # Open modal with text inputs
                client.views_open(
                    trigger_id=body['trigger_id'],
                    view=self._build_edit_modal(suggestion)
                )
                
                logger.info(f"Opened edit modal for {buffer_id}")
                
            except Exception as e:
                logger.error(f"Error handling edit: {e}")
        
                logger.error(f"Error handling edit: {e}")
        
        @self.slack.app.action("retry_suggestion")
        def handle_retry(ack, body, client):
            """Handle Retry button click."""
            ack()
            
            try:
                buffer_id = body['actions'][0]['value']
                channel_id = body['channel']['id']
                
                # Post "regenerating" message
                client.chat_postMessage(
                    channel=channel_id,
                    text="🔄 Regenerating suggestion... please wait.",
                    thread_ts=body['message']['ts']
                )
                
                # Fetch original buffer data
                buffer = self.storage.get_buffer_data(buffer_id)
                if not buffer:
                    logger.error(f"Buffer not found for retry: {buffer_id}")
                    return
                
                # Call ghostwriter to regenerate
                # Note: We need access to ghostwriter instance here
                if hasattr(self, 'ghostwriter'):
                    # Generate new suggestion
                    new_suggestion = self.ghostwriter.generate_suggestions(buffer)
                    if new_suggestion:
                        # Post new card (as a new message)
                        self.post_suggestion(new_suggestion)
                        logger.info(f"Retried and posted new suggestion for {buffer_id}")
                    else:
                        client.chat_postMessage(
                            channel=channel_id,
                            text="❌ Failed to regenerate suggestion. Content might not be suitable."
                        )
                else:
                    logger.error("Ghostwriter instance not available in InteractionHandler")
                    
            except Exception as e:
                logger.error(f"Error handling retry: {e}")
        
        @self.slack.app.action("refine_suggestion")
        def handle_refine(ack, body, client):
            """Handle Refine button click."""
            ack()
            
            try:
                buffer_id = body['actions'][0]['value']
                suggestion = self.storage.get_suggestion(buffer_id)
                
                if not suggestion:
                    logger.error(f"Suggestion not found for refine: {buffer_id}")
                    return
                
                # Open modal with text input for instructions
                client.views_open(
                    trigger_id=body['trigger_id'],
                    view=self._build_refine_modal(suggestion)
                )
                
                logger.info(f"Opened refine modal for {buffer_id}")
                
            except Exception as e:
                logger.error(f"Error handling refine: {e}")

        @self.slack.app.action("approve_suggestion")
        def handle_approve(ack, body, client):
            """Handle Approve button click."""
            ack()
            
            try:
                buffer_id = body['actions'][0]['value']
                suggestion = self.storage.get_suggestion(buffer_id)
                
                if not suggestion:
                    logger.error(f"Suggestion not found: {buffer_id}")
                    return
                
                # Update database
                self.storage.record_user_action(buffer_id, "approved")
                
                # Update message to show approval header but KEEP content
                original_blocks = body['message']['blocks']
                
                # Replace the actions block (buttons) with approved status
                new_blocks = [b for b in original_blocks if b['type'] != 'actions']
                
                # Add approval header at the top
                approval_header = {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "✅ *Suggestion Approved!* (Ready to copy)"
                    }
                }
                new_blocks.insert(0, approval_header)
                
                client.chat_update(
                    channel=body['channel']['id'],
                    ts=body['message']['ts'],
                    text="✅ Suggestion approved!",
                    blocks=new_blocks
                )
                
                logger.info(f"Approved suggestion {buffer_id}")
                
            except Exception as e:
                logger.error(f"Error handling approve: {e}")
        
        @self.slack.app.action("dismiss_suggestion")
        def handle_dismiss(ack, body, client):
            """Handle Dismiss button click."""
            ack()
            
            try:
                buffer_id = body['actions'][0]['value']
                
                # Update database
                self.storage.record_user_action(buffer_id, "dismissed")
                
                # Delete message
                client.chat_delete(
                    channel=body['channel']['id'],
                    ts=body['message']['ts']
                )
                
                logger.info(f"Dismissed suggestion {buffer_id}")
                
            except Exception as e:
                logger.error(f"Error handling dismiss: {e}")
        
        @self.slack.app.view("edit_modal_submit")
        def handle_modal_submit(ack, body, client, view):
            """Handle modal submission after editing."""
            ack()
            
            try:
                buffer_id = view['private_metadata']
                values = view['state']['values']
                
                # Extract edited drafts
                x_draft = values['x_draft_input']['x_draft']['value']
                linkedin_draft = values['linkedin_draft_input']['linkedin_draft']['value']
                
                # Update database
                self.storage.update_suggestion(buffer_id, {
                    'x_draft': x_draft,
                    'linkedin_draft': linkedin_draft
                })
                self.storage.record_user_action(buffer_id, "edited")
                
                logger.info(f"Updated suggestion {buffer_id} with edited content")
                
                # Post confirmation message
                suggestion = self.storage.get_suggestion(buffer_id)
                if suggestion:
                    channel_id = body['user']['id']  # DM the user
                    client.chat_postMessage(
                        channel=channel_id,
                        text="✏️ Your edits have been saved!"
                    )
                
            except Exception as e:
                logger.error(f"Error handling modal submit: {e}")

        @self.slack.app.view("refine_modal_submit")
        def handle_refine_submit(ack, body, client, view):
            """Handle modal submission for refinement."""
            ack()
            
            try:
                buffer_id = view['private_metadata']
                values = view['state']['values']
                instruction = values['refine_instruction_input']['refine_instruction']['value']
                
                # Post "refining" message using user ID as channel for DM or the original channel?
                # Using user ID is safer for notifications, but we want to update the original message stream
                # Let's post a thread reply saying we are refining
                
                # We need the channel ID, which is tricky from view submission
                # but we can try to find the buffer data which has channel_id
                buffer = self.storage.get_buffer_data(buffer_id)
                if not buffer:
                     logger.error(f"Buffer not found for refine: {buffer_id}")
                     return

                client.chat_postMessage(
                    channel=buffer.channel_id,
                    text=f"✨ Refining suggestion based on: '{instruction}'...",
                    thread_ts=self.storage.get_suggestion(buffer_id).get('message_ts')
                )
                
                # Call ghostwriter to regenerate with instruction
                if hasattr(self, 'ghostwriter'):
                    new_suggestion = self.ghostwriter.generate_suggestions(buffer, refinement_instruction=instruction)
                    
                    if new_suggestion:
                        self.post_suggestion(new_suggestion)
                        logger.info(f"Refined and posted new suggestion for {buffer_id}")
                    else:
                         client.chat_postMessage(
                            channel=buffer.channel_id,
                            text="❌ Failed to refine suggestion."
                        )
                else:
                    logger.error("Ghostwriter instance not available")
                    
            except Exception as e:
                logger.error(f"Error handling refine submit: {e}")
    
    def post_suggestion(self, suggestion: Dict):
        """
        Post suggestion card to Slack.
        
        Args:
            suggestion: Dict with x_draft, linkedin_draft, etc.
        """
        try:
            blocks = self._build_suggestion_card(suggestion)
            
            response = self.slack.post_message(
                channel_id=suggestion['channel_id'],
                blocks=blocks,
                text=f"💡 Content suggestion: {suggestion['topic']}"
            )
            
            # Store message timestamp for later updates
            if response and 'ts' in response:
                suggestion['message_ts'] = response['ts']
                self.storage.save_suggestion(suggestion)
                logger.info(f"Posted suggestion card for {suggestion['buffer_id']}")
            
        except Exception as e:
            logger.error(f"Error posting suggestion: {e}")
    
    def _build_suggestion_card(self, suggestion: Dict) -> list:
        """
        Build Block Kit blocks for suggestion card.
        
        Args:
            suggestion: Dict with suggestion data
        
        Returns:
            List of Block Kit blocks
        """
        # Format time range
        try:
            start = datetime.fromisoformat(suggestion['start_time'])
            end = datetime.fromisoformat(suggestion['end_time'])
            time_range = f"{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}"
        except:
            time_range = "earlier today"
        
        return [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "💡 Content Suggestion",
                    "emoji": True
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Topic:* {suggestion['topic']} | *Confidence:* {suggestion['confidence']:.0%}"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🐦 For X (Twitter):*\n```{suggestion['x_draft']}```"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*💼 For LinkedIn:*\n```{suggestion['linkedin_draft']}```"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📅 Based on your conversation from {time_range}"
                    }
                ]
            },
            {
                "type": "actions",
                "block_id": f"suggestion_{suggestion['buffer_id']}",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✏️ Edit",
                            "emoji": True
                        },
                        "action_id": "edit_suggestion",
                        "value": suggestion['buffer_id']
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "👍 Approve",
                            "emoji": True
                        },
                        "style": "primary",
                        "action_id": "approve_suggestion",
                        "value": suggestion['buffer_id']
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🔄 Retry",
                            "emoji": True
                        },
                        "action_id": "retry_suggestion",
                        "value": suggestion['buffer_id']
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✨ Refine",
                            "emoji": True
                        },
                        "action_id": "refine_suggestion",
                        "value": suggestion['buffer_id']
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🗑️ Dismiss",
                            "emoji": True
                        },
                        "style": "danger",
                        "action_id": "dismiss_suggestion",
                        "value": suggestion['buffer_id']
                    }
                ]
            }
        ]
    
    def _build_edit_modal(self, suggestion: Dict) -> Dict:
        """
        Build modal for editing drafts.
        
        Args:
            suggestion: Dict with suggestion data
        
        Returns:
            Modal view dict
        """
        return {
            "type": "modal",
            "callback_id": "edit_modal_submit",
            "private_metadata": suggestion['suggestion_id'],
            "title": {
                "type": "plain_text",
                "text": "Edit Suggestion"
            },
            "submit": {
                "type": "plain_text",
                "text": "Save"
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel"
            },
            "blocks": [
                {
                    "type": "input",
                    "block_id": "x_draft_input",
                    "label": {
                        "type": "plain_text",
                        "text": "🐦 X (Twitter) Draft"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "x_draft",
                        "multiline": True,
                        "initial_value": suggestion['x_draft'],
                        "max_length": 280
                    }
                },
                {
                    "type": "input",
                    "block_id": "linkedin_draft_input",
                    "label": {
                        "type": "plain_text",
                        "text": "💼 LinkedIn Draft"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "linkedin_draft",
                        "multiline": True,
                        "initial_value": suggestion['linkedin_draft']
                    }
                }
            ]
        }
        
    def _build_refine_modal(self, suggestion: Dict) -> Dict:
        """
        Build modal for refinement instructions.
        
        Args:
            suggestion: Dict with suggestion data
        
        Returns:
            Modal view dict
        """
        return {
            "type": "modal",
            "callback_id": "refine_modal_submit",
            "private_metadata": suggestion['suggestion_id'],
            "title": {
                "type": "plain_text",
                "text": "Refine Content"
            },
            "submit": {
                "type": "plain_text",
                "text": "Regenerate"
            },
            "close": {
                "type": "plain_text",
                "text": "Cancel"
            },
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "💡 *How should we improve these drafts?*"
                    }
                },
                {
                    "type": "input",
                    "block_id": "refine_instruction_input",
                    "label": {
                        "type": "plain_text",
                        "text": "Instructions"
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "refine_instruction",
                        "multiline": True,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "e.g., 'Make it more professional', 'Focus on the technical details', 'Use a punchier hook'"
                        }
                    }
                }
            ]
        }
