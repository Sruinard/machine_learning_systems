import pytest
import collect_reviews

def test_can_collect_user_reviews_for_xbox():
    XBOX_ASIN = "B0BCXJ8BF4"
    reviews = collect_reviews.retrieve_product_reviews_from_amazon(XBOX_ASIN)
    assert len(reviews) > 0

def test_can_store_and_retrieve_review_from_db():
    class FakeDBRepository:
        def __init__(self):
            self.reviews = []
        def insert_review(self, review):
            self.reviews.append(review)
        def get_all_reviews(self):
            return self.reviews

    db = FakeDBRepository()
    review = collect_reviews.Review(
        id="1",
        product_id="B0BCXJ8BF4",
        title="Great product",
        content="I love it",
        rating=5,
        date="2020-01-01",
        verified_purchase=True,
    )
    db.insert_review(review)
    assert db.get_all_reviews() == [review]